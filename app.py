import asyncio
import os
import logging
import time,requests
from config import *
from database import *
from tools import split_video, gen_thumb, print_progress_bar
from myjd import (
    connect_to_jd,
    add_links,
    clear_downloads,
    process_and_move_links,
    check_for_new_links,
)
from scraper import fetch_page
import random
import string
from upload import switch_upload,upload_thumb


# Setup logging
logging.basicConfig(level=logging.INFO)

downloaded_files = []

# Connect to MongoDB
db = connect_to_mongodb(MONGODB_URI, "Spidydb")
collection_name = COLLECTION_NAME

if db is not None:
    logging.info("Connected to MongoDB")



async def process_file(url,directory_path):
    """Processes files in the given directory to generate thumbnails and clean up."""
    try:
        if not os.path.exists(directory_path):
            logging.error(f"Directory does not exist: {directory_path}")
            return        
        for file_name in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file_name)

            if os.path.isfile(file_path):
                thumbnail_name = f"{file_name}_thumb.png"
                logging.info(f"Generating thumbnail for {file_path}...")
                # Generate the thumbnail
                gen_thumb(file_path, thumbnail_name)
                logging.info(f"Thumbnail generated: {thumbnail_name}")
                document = {"URL":url}
                insert_document(db, collection_name, document)
                # Remove the original file
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logging.info(f"Removed original file: {file_path}")
                # Remove the thumbnail if needed
                if os.path.exists(thumbnail_name):
                    os.remove(thumbnail_name)
                    logging.info(f"Removed thumbnail: {thumbnail_name}")
                return
            else:
                logging.warning(f"Skipping non-file item: {file_path}")
    except FileNotFoundError as e:
        logging.error(f"File not found error: {e}")
    except Exception as e:
        logging.error(f"Error processing upload: {e}")


async def check_downloads(device,url,path):
    """Check for completed downloads and process them."""
    while True:
        try:
            downloads = device.downloads.query_links()
            if not downloads:
                logging.info("No active downloads.")
            else:
                for download in downloads:
                    if download['bytesTotal'] == download['bytesLoaded']:
                        # Download is complete
                        if download['name'] not in downloaded_files:
                            print_progress_bar(download['name'], download['bytesLoaded'], download['bytesTotal'])
                            downloaded_files.append(download['name'])
                            logging.info(f"Download completed: {download['name']}")
                            logging.info(path)
                            await process_file(url,path)  # Process the downloaded file
                            return
                    else:
                        # Still downloading
                        print_progress_bar(download['name'], download['bytesLoaded'], download['bytesTotal'])

            await asyncio.sleep(2)  # Pause before checking again
        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
            await asyncio.sleep(2)  # Pause before retrying

async def start_download():
    """Main download function."""
    try:
        # Connect to JD device
        jd = connect_to_jd(JD_APP_KEY, JD_EMAIL, JD_PASSWORD)
        device = jd.get_device(JD_DEVICENAME)
        logging.info('Connected to JD device')
        clear_downloads(device)
        logging.info('Fetching Links....')
        video_links = fetch_page()
        logging.info(f"Total links found: {len(video_links)}")
        downloaded = [ data["URL"] for data in find_documents(db, collection_name)]
        if video_links:
            for url in video_links:
              if url not in downloaded:
                hash_code = generate_random_string(5)
                response = add_links(device, url, "Draft",hash_code)
                check_for_new_links(device, device.linkgrabber)
                process_and_move_links(device)
                await check_downloads(device,url,f"downloads/")
    
    except Exception as e:
        logging.error(f"Error in start_download: {e}")

if __name__ == "__main__":
    asyncio.run(start_download())
