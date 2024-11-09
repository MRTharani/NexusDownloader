from pyrogram import Client
import asyncio
import os,time
import logging
import time,requests
from config import *
from database import *
from tools import split_video, gen_thumb, print_progress_bar
from myjd import (
    connect_to_jd,
    add_links,
    clear_downloads,
    move_links,
    check_for_new_links,
)
from scraper import main_fetch
from upload import switch_upload,upload_thumb

# Setup logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Connect to MongoDB
db = connect_to_mongodb(MONGODB_URI, "Spidydb")
collection_name = COLLECTION_NAME

if db is not None:
    logging.info("Connected to MongoDB")

# Initialize the Telegram client
app = Client(
    name="NexusDL-bot",
    api_hash=API_HASH,
    api_id=API_ID,
    bot_token=BOT_TOKEN,
    workers=30
)

downloaded_files  = []


async def process_file(app, url, directory_path):
    """Processes files in the given directory to generate thumbnails and clean up."""
    try:
        time.sleep(10)
        if not os.path.exists(directory_path):
            logging.error(f"Directory does not exist: {directory_path}")
            return        

        for file_name in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file_name)
            if os.path.isfile(file_path):
                if "draftsex" in url:
                        title = url.split("/")[-1].replace("html", "mp4").title()
                elif "missav" in url:
                        title = url.split("/")[-1].title()
                os.rename(file_path , os.path.join(directory_path, title))
                file_path = os.path.join(directory_path, title)
            
                thumbnail_name = f"{file_name}_thumb.png"
                try:
                    logging.info(f"Generating thumbnail for {file_path}...")
                    gen_thumb(file_path, thumbnail_name)
                    logging.info(f"Thumbnail generated: {thumbnail_name}")
                    
                    file_size = os.path.getsize(file_path)
                    threshold_size = 1.9 * (1024 ** 3)  # 1.9 GB in bytes
                    
                    if file_size <= threshold_size:  # Check the condition properly
                        vid = await app.send_video(DUMP_ID, file_path, thumb=thumbnail_name, caption=title)
                        document = {"ID": vid.id, "URL": url}
                        insert_document(db, collection_name, document)
                        logging.info(f"Video sent and document inserted: {document}")

                    # Clean up files
                    for f in [file_path, thumbnail_name]:
                        if os.path.exists(f):
                            os.remove(f)
                            logging.info(f"Removed file: {f}") 
                except Exception as e:
                    logging.error(f"Error processing file {file_name}: {e}")
                    
            else:
                logging.warning(f"Skipping non-file item: {file_path}")
    except Exception as e:
        logging.error(f"Error processing upload: {e}")


async def check_downloads(app,device,url,path):
    """Check for completed downloads and process them."""
    while True:
        try:
            downloads = device.downloads.query_links()
            if not downloads:
                logging.info("No active downloads.")
            else:
                for download in downloads:
                    if download['bytesTotal'] >= download['bytesLoaded'] or ("running" in download and not download['running']):
                        # Download is complete
                        if download['name'] not in downloaded_files:
                            print_progress_bar(download['name'], download['bytesLoaded'], download['bytesTotal'])
                            downloaded_files.append(download['name'])
                            logging.info(f"Download completed: {download['name']}")
                            logging.info(path)
                            await process_file(app,url,path)  # Process the downloaded file
                            return
                    else:
                        print_progress_bar(download['name'], download['bytesLoaded'], download['bytesTotal'])

            await asyncio.sleep(2)  # Pause before checking again
        except Exception as e:
            logging.error(f"Unexpected Error: {e}")
            await asyncio.sleep(2)  # Pause before retrying





async def start_download():
  async with app:
    try:
        # Connect to JD device
        jd = connect_to_jd(JD_APP_KEY, JD_EMAIL, JD_PASSWORD)
        device = jd.get_device(JD_DEVICENAME)
        logging.info('Connected to JD device')
        clear_downloads(device)
        
        downloaded = [ data["URL"] for data in find_documents(db, collection_name)]

        logging.info('Fetching Links....')
        video_links = await main_fetch(downloaded)
        logging.info(f"Total links found: {len(video_links)}")

        if video_links:
            for url in video_links:


              if url not in downloaded or True:
                logging.info(f"Processing link : {url}")
                directory = hash(url.split("/")[-1])
                response = add_links(device, url, "Videos",directory)
                check_for_new_links(device, device.linkgrabber)
                if "draftsex" in url:
                    move_links(device, draft_condition=True)
                elif "missav" in url:
                    move_links(device, jav_condition=True)
                elif "pornhub" in url:
                    move_links(device, ph_condition=True)



                await check_downloads(app,device,url,f"downloads/{directory}")
                clear_downloads(device)
    except Exception as e:
        logging.error(f"Error in start_download: {e}")

if __name__ == "__main__":
    app.run(start_download())


