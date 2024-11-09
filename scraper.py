import os
import random
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright
import asyncio
import logging
import subprocess
import json




logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def jav_fetch_links(url,suffix):
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
            links = [link['href'] for link in soup.find_all('a', href=True) if link["href"].endswith(suffix) and link["href"].startswith("https://missav.com/en/") ]
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
        links = [base_url + div.find('a', class_='thumbnailTitle')['href'] for div in soup.find_all('div', class_='vidTitleWrapper') if div.find('a', class_='thumbnailTitle')]
        logging.info(f"Fetched {len(links)} Pornhub links")
        return links
    except requests.RequestException as e:
        logging.error(f"Error fetching links from Pornhub: {e}")
        return []


def extract_urls(url):
    """Extract URLs from a given video URL using yt-dlp."""
    logging.info(f"Starting to extract URLs from {url}")
    
    try:
        # Run yt-dlp and capture the output directly
        result = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-j", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        
        # Parse JSON lines from yt-dlp output
        urls = []
        for line in result.stdout.splitlines():
            data = json.loads(line)
            if "url" in data:
                urls.append(data["url"])

        logging.info(f"Extracted {len(urls)} URLs from {url}")
        return urls
    
    except subprocess.CalledProcessError as e:
        logging.error(f"yt-dlp command failed for {url}: {e.stderr}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON output for {url}: {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error extracting URLs from {url}: {e}")
        return []


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
    #ph_links = fetch_pornhub_links()
    #urls.extend(ph_links)
    logging.info(f"Total combined links fetched: {len(urls)}")
    return random.sample(urls, min(200, len(urls)))





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





# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_draft_links():
    # Initialize a session to reuse across requests
    session = requests.Session()

    def extract_links_from_page(url, link_filter):
        """Extract links from a given page based on the filter function."""
        logging.info(f"Extracting links from {url}")
        try:
            response = session.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                # Extract relevant links based on the provided filter function
                links = [a.get('href') for a in soup.find_all('a', href=True) if link_filter(a.get('href'))]
                logging.info(f"Extracted {len(links)} links from {url}")
                return links
            else:
                logging.warning(f"Failed to retrieve {url} with status code: {response.status_code}")
                return []
        except requests.RequestException as e:
            logging.error(f"Error retrieving {url}: {e}")
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
        logging.info(f"Processing pages for base URL: {base_url}")
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit page fetching tasks in parallel
            future_to_url = {executor.submit(extract_links_from_page, f"{base_url}/page{page}.html", link_filter): page for page in page_range}
            
            for future in future_to_url:
                page = future_to_url[future]
                try:
                    links = future.result()
                    all_links.extend(links)
                    logging.info(f"Page {page} processed with {len(links)} links found")
                except Exception as e:
                    logging.error(f"Error processing page {page} at {base_url}: {e}")
        return all_links

    # Collect video links from different categories
    categories = ["top-rated", "most-viewed", "most-recent"]
    video_links = []
    for category in categories:
        logging.info(f"Collecting video links for category: {category}")
        cat_links = process_pages(f'https://draftsex.porn/{category}', range(10), filter_video_links)
        video_links.extend(cat_links)
    
    # Collect model links
    logging.info("Collecting model links")
    model_links = process_pages('https://draftsex.porn/models', range(100), filter_model_links)
    
    # Process model links to collect additional video links
    vids = []
    logging.info("Processing model links to collect additional video links")
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(extract_links_from_page, url, filter_video_links): url for url in model_links}
        
        for future in future_to_url:
            url = future_to_url[future]
            try:
                extracted_vids = future.result()
                vids.extend(extracted_vids)
                logging.info(f"Processed model URL {url} with {len(extracted_vids)} additional video links found")
            except Exception as e:
                logging.error(f"Error processing model URL {url}: {e}")

    # Return or print the total links collected
    logging.info("Link collection completed")
    return vids



# Main Execution
async def main_fetch(downloads):
    logging.info("Starting main fetch process")
    try:
        jav_links = []
        i = 1
        while  True:
            url = f'https://missav.com/dm561/en/uncensored-leak?page={i}'        
            links = await jav_fetch_links(url,"uncensored-leak")
            jav_links.extend(links)
            if len(jav_links) >= 200:
                    break
            i +=1
        draft_links = fetch_draft_links()
        urls = jav_links + draft_links
        links = [ link for link in urls if link not in downloads ]

        logging.info(f"Total links fetched: {len(links)}")
        return random.sample(links, min(100, len(links)))
    except Exception as e:
        logging.error(f"An error occurred during execution: {e}")
