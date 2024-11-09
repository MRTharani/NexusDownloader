import myjdapi
import asyncio
import time
import logging
from tools import print_progress_bar
import os


# Configure logging
logging.basicConfig(level=logging.INFO)



def connect_to_jd(app_key, email, password):
    """Connect to JDownloader and handle connection retries."""
    jd = myjdapi.Myjdapi()
    jd.set_app_key(app_key)

    connected = False
    while not connected:
        try:
            logging.info("Waiting for JD to Start")
            #time.sleep(100)
            jd.connect(email, password)
            jd.update_devices()
            connected = True
            logging.info('Connected to My.JDownloader successfully.')
        except myjdapi.exception.MYJDConnectionException as e:
            logging.error(f"Failed to connect to My.JDownloader: {e}")
            logging.info("Retrying in 10 seconds...")
            time.sleep(10)

    return jd

def clear_downloads(device):
    """Clear all active downloads on the JDownloader device."""
    try:
        downloads = device.downloads.query_links()
        if downloads:
            for i in downloads:
                device.downloads.remove_links([i["uuid"]], [i['packageUUID']])
            logging.info("All downloads cleared.")
        else:
            logging.info("No active downloads to clear.")
    except myjdapi.exception.MYJDConnectionException as e:
        logging.error(f"Failed to clear downloads: {e}")

def add_links(device, url, package_name,directory):
    """Add links to the Linkgrabber with the specified package name."""
    folder = f"/jdownloader/downloads/{directory}"

    # Ensure the destination folder exists (consider implementing this if needed)
    
    linkgrabber = device.linkgrabber
    try:
        res = linkgrabber.add_links([{
            "autostart": False,
            "links": url,
            "packageName": package_name,
            "extractPassword": None,
            "priority": "DEFAULT",
            "downloadPassword": None,
            "destinationFolder": folder,
            "overwritePackagizerRules": True
        }])
        return res
    except myjdapi.exception.MYJDConnectionException as e:
        logging.error(f"Failed to add links: {e}")
        return None


def check_for_new_links(device, linkgrabber):
    """Wait until new links are detected in the Linkgrabber."""
    seen_links = set()
    while True:
        try:
            current_links = linkgrabber.query_links()
            current_urls = {link['url'] for link in current_links}
            new_links = current_urls - seen_links

            if new_links:
                logging.info(f"New links detected")
                seen_links.update(new_links)
                return current_links
            else:
                logging.info("No new links found. Waiting...")
                time.sleep(3)

        except myjdapi.exception.MYJDConnectionException as e:
            logging.error(f"MYJD Connection Error: {e}")
        except Exception as e:
            logging.error(f"Unexpected Errorg: {e}")



def move_links(device, draft_condition=False,jav_condition=False,ph_condition=False):
    """Move links to download list based on a custom filter condition."""
    time.sleep(10)
    linkgrabber = device.linkgrabber
    downloads = device.downloads.query_links()
    downloaded_files = {link['name'] for link in downloads}
    link_list = linkgrabber.query_links()
    
    package_ids = []
    link_ids = []

    for link in link_list:
        file_name = link['name']
        if file_name not in downloaded_files:
                if jav_condition:
                    if "rapidgator" not in link["url"]:
                        package_ids.append(link.get('packageUUID'))
                        link_ids.append(link.get('uuid'))
                elif draft_condition:
                    if link['name'].endswith(('mp4', 'mkv')):
                        package_ids.append(link.get('packageUUID'))
                        link_ids.append(link.get('uuid'))
                elif ph_condition:
                    logging.info( file_name)
                    if "720" in link['name'] and "hls" in link['name']:
                        package_ids.append(link.get('packageUUID'))
                        link_ids.append(link.get('uuid'))
    if link_ids:
        try:
            linkgrabber.move_to_downloadlist(link_ids, package_ids)
            logging.info("Moved new links to download list.")
            time.sleep(5)
            linkgrabber.clear_list()
        except myjdapi.exception.MYJDConnectionException as e:
            logging.error(f"Failed to move links to download list: {e}")
    else:
        logging.info("No new links to move to the download list.")


