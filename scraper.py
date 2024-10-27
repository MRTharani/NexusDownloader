import os
import random
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def jav_fetch_links(url):
    """Fetch links from a specific site using Playwright."""
    logging.info(f"Starting to fetch links from {url}")
    async with async_playwright() as p:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        try:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=user_agent)

            page = await context.new_page()
            await page.goto(url)
            await page.wait_for_load_state('networkidle')
            content = await page.content()
            await page.close()

            soup = BeautifulSoup(content, 'html.parser')
            links = [link['href'] for link in soup.find_all('a', href=True)]
            logging.info(f"Fetched {len(links)} links from {url}")
            return links
        except Exception as e:
            logging.error(f"Error during fetching links from {url}: {e}")
            return []
        finally:
            await browser.close()

def fetch_pornhub_links(query=None):
    """Fetch video links from Pornhub or search based on a query."""
    logging.info("Starting to fetch Pornhub links")
    base_url = "https://www.pornhub.com"
    search_url = f"https://www.pornhub.com/video/search?search={query}" if query else base_url
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = [div.find('a', class_='thumbnailTitle')['href'] for div in soup.find_all('div', class_='vidTitleWrapper') if div.find('a', class_='thumbnailTitle')]
        logging.info(f"Fetched {len(links)} Pornhub links")
        return links
    except requests.RequestException as e:
        logging.error(f"Error fetching links from Pornhub: {e}")
        return []

def extract_urls(url):
    """Extract URLs from a given video URL using yt-dlp."""
    logging.info(f"Starting to extract URLs from {url}")
    temp_file = "dump.txt"
    try:
        os.system(f"yt-dlp --flat-playlist -j {url} > {temp_file}")
        with open(temp_file) as file:
            urls = [line.strip().split('"url":')[1].strip().strip('"') for line in file if '"url":' in line]
        logging.info(f"Extracted {len(urls)} URLs from {url}")
        return urls
    except Exception as e:
        logging.error(f"Error extracting URLs from {url}: {e}")
        return []
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def fetch_models():
    """Fetch model links from Pornhub."""
    logging.info("Starting to fetch model links from Pornhub")
    urls = [
        "https://www.pornhub.com/pornstars?performerType=amateur#subFilterListVideos",
    ]
    try:
        response = requests.get(random.choice(urls))
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        model_links = list(set("https://www.pornhub.com" + link.get('href') for link in soup.find_all('a') if link.get('href') and ("/model/" in link.get('href') or "/pornstar/" in link.get('href'))))
        logging.info(f"Fetched {len(model_links)} model links")
        return model_links
    except requests.RequestException as e:
        logging.error(f"Error fetching model links: {e}")
        return []

def fetch_combined_links():
    """Fetch combined links from various sources."""
    logging.info("Started combined link generation")
    urls = []
    
    # Fetch model links
    for model_link in fetch_models()[:3]:
        logging.info(f"Fetching URLs from model link: {model_link}")
        urls.extend(extract_urls(model_link))
    
    # Fetch video links
    ph_links = fetch_pornhub_links()
    urls.extend(ph_links)
    logging.info(f"Total combined links fetched: {len(urls)}")
    return random.sample(urls, min(100, len(urls)))





'''
async def fetch_draft_links():
    """Fetch video and model links from DraftSex using Playwright."""
    logging.info("Starting to fetch DraftSex links")
    async with async_playwright() as p:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()

        async def extract_links_from_page(url, link_filter):
            logging.info(f"Extracting links from {url}")
            try:
                await page.goto(url)
                await page.wait_for_load_state('networkidle')
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')
                links = [a.get('href') for a in soup.find_all('a', href=True) if link_filter(a.get('href'))]
                logging.info(f"Extracted {len(links)} links from {url}")
                return links
            except Exception as e:
                logging.error(f"Error retrieving {url}: {e}")
                return []

        def filter_links(href, link_type):
            return f"https://draftsex.porn/{link_type}/" in href

        async def process_pages(base_url, page_range, link_type):
            all_links = []
            for page_num in page_range:
                url = f"{base_url}/{link_type}/page{page_num}.html"
                links = await extract_links_from_page(url, lambda href: filter_links(href, link_type))
                all_links.extend(links)
            logging.info(f"Total {link_type} links fetched: {len(all_links)}")
            return all_links

        # Collect video and model links
        video_links = await process_pages('https://draftsex.porn', range(1, 11), 'video')  # Adjust range as necessary
        model_links = await process_pages('https://draftsex.porn/models', range(1, 101), 'models')

        # Extract further video links from models
        vids = []
        for model_url in model_links:
            vids.extend(await extract_links_from_page(model_url, lambda href: filter_links(href, 'video')))
        
        await browser.close()
        logging.info(f"Total links fetched from DraftSex: {len(video_links) + len(vids)}")
        return video_links + vids'''



def fetch_draft_links():
    # Initialize a session to reuse across requests
    session = requests.Session()

    def extract_links_from_page(url, link_filter):
        """Extract links from a given page based on the filter function."""
        try:
            response = session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Extract relevant links based on the provided filter function
                links = [a.get('href') for a in soup.find_all('a', href=True) if link_filter(a.get('href'))]
                return links
            else:
                return []
        except requests.RequestException as e:
            print(f"Error retrieving {url}: {e}")
            return []

    def filter_video_links(href):
        """Filter for video links."""
        return "https://draftsex.porn/video/" in href

    def filter_model_links(href):
        """Filter for model links."""
        return "https://draftsex.porn/models/" in href and "html" in href

    def process_pages(base_url, page_range, link_filter):
        """Process multiple pages in parallel and extract links."""
        all_links = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit page fetching tasks in parallel
            future_to_url = {executor.submit(extract_links_from_page, f"{base_url}/page{page}.html", link_filter): page for page in page_range}
            
            for future in future_to_url:
                links = future.result()
                all_links.extend(links)
        return all_links

    

    # Step 21: Collect all video links from categories
    cats = ["top-rated", "most-viewed", "most-recent"]
    video_links = []
    for cat in cats:
        cat_links = process_pages(f'https://draftsex.porn/{cat}', range(10), filter_video_links)
        video_links.extend(cat_links)
    

    # Step 2: Collect all model links
    model_links = process_pages('https://draftsex.porn/models', range(100), filter_model_links)
    
    
    # Step 3: Process all collected links to extract further video links
    vids = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(extract_links_from_page, url, filter_video_links): url for url in model_links}
        
        for future in future_to_url:
            extracted_vids = future.result()
            vids.extend(extracted_vids)

    # Return or print the total links collected
    return vids


# Main Execution
async def main_fetch():
    logging.info("Starting main fetch process")
    try:
        jav_links = []
        urls = [
            "https://missav.com/dm559/en/uncensored-leak",
            "https://missav.com/dm513/en/new",
            "https://missav.com/dm242/en/today-hot"
        ]
        
        for url in urls:
            links = await jav_fetch_links(url)
            jav_links.extend(links)
        
        ph_links = fetch_combined_links()
        draft_links = fetch_draft_links()
        links = ph_links + draft_links + jav_links
        
        logging.info(f"Total links fetched: {len(links)}")
        return random.sample(links, min(100, len(links)))
    except Exception as e:
        logging.error(f"An error occurred during execution: {e}")
