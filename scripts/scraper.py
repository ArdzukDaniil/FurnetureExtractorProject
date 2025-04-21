import requests
from bs4 import BeautifulSoup
import json
import os
import logging
import time
from typing import List, Dict, Optional

URL_LIST_FILE = "../data/urls.txt"
OUTPUT_DIR = os.path.join("../data", "raw_texts")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "scraped_texts.json")
NUM_URLS_TO_PROCESS = 500
TARGET_SUCCESSFUL_PAGES = 150
REQUEST_TIMEOUT = 20
SLEEP_INTERVAL = 1
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_urls(filepath: str) -> List[str]:
    try:
        with open(filepath, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
        logging.info(f"Loaded {len(urls)} URLs from {filepath}")
        return urls
    except FileNotFoundError:
        logging.error(f"URL file not found: {filepath}")
        return []
    except Exception as e:
        logging.error(f"Error reading URL file {filepath}: {e}")
        return []

def extract_text_from_html(html_content: str) -> Optional[str]:
    if not html_content:
        return None
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "link", "meta"]):
            tag.decompose()

        main_content = soup.find("main")
        if not main_content:
            main_content = soup.find("article")
        if not main_content:
            common_containers = ["#content", "#main-content", ".content", ".main", ".product-details"]
            for selector in common_containers:
                main_content = soup.select_one(selector)
                if main_content:
                    break
        if not main_content:
            main_content = soup.body

        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
            cleaned_text = " ".join(text.split())
            if len(cleaned_text) > 50:
                return cleaned_text
            else:
                logging.warning("Extracted text seems too short, might be non-content page.")
                full_text = soup.get_text(separator=" ", strip=True)
                cleaned_full_text = " ".join(full_text.split())
                if len(cleaned_full_text) > 50:
                    logging.warning("Falling back to full soup text extraction.")
                    return cleaned_full_text
                else:
                    return None
        else:
            logging.warning("Could not find main content or body tag.")
            return None
    except Exception as e:
        logging.error(f"Error parsing HTML: {e}")
        return None

def scrape_url(url: str) -> Optional[Dict[str, str]]:
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type:
            logging.warning(f"Skipping URL {url} - Content-Type is not HTML ({content_type})")
            return None
        html_content = response.text
        logging.info(f"Successfully fetched URL: {url}")
        extracted_text = extract_text_from_html(html_content)
        if extracted_text:
            return {"url": url, "text": extracted_text}
        else:
            logging.warning(f"No meaningful text extracted from URL: {url}")
            return None
    except requests.exceptions.Timeout:
        logging.warning(f"Request timed out for URL: {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logging.warning(f"HTTP Error for URL {url}: {e.response.status_code} {e.response.reason}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not fetch or process URL: {url}. Error: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing {url}: {e}")
        return None

if __name__ == "__main__":
    logging.info("Starting scraper script...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logging.info(f"Output directory set to: {OUTPUT_DIR}")
    urls_to_scrape = load_urls(URL_LIST_FILE)
    if not urls_to_scrape:
        logging.info("No URLs to process. Exiting.")
        exit()
    all_scraped_data: List[Dict[str, str]] = []
    processed_count = 0
    successful_count = 0
    failed_count = 0
    logging.info(f"Attempting to scrape up to {NUM_URLS_TO_PROCESS} URLs to get {TARGET_SUCCESSFUL_PAGES} successful pages.")
    for i, url in enumerate(urls_to_scrape):
        if processed_count >= NUM_URLS_TO_PROCESS:
            logging.info(f"Reached processing limit of {NUM_URLS_TO_PROCESS} URLs.")
            break
        if successful_count >= TARGET_SUCCESSFUL_PAGES:
            logging.info(f"Reached target of {TARGET_SUCCESSFUL_PAGES} successfully scraped pages.")
            break
        logging.info(f"Processing URL {i+1}/{len(urls_to_scrape)}: {url}")
        processed_count += 1
        result = scrape_url(url)
        if result:
            all_scraped_data.append(result)
            successful_count += 1
            logging.info(f"Success! Pages collected: {successful_count}/{TARGET_SUCCESSFUL_PAGES}")
        else:
            failed_count += 1
        if i < len(urls_to_scrape) - 1:
            logging.info(f"Sleeping for {SLEEP_INTERVAL} second(s)...")
            time.sleep(SLEEP_INTERVAL)
    logging.info(f"Scraping finished. Total URLs processed: {processed_count}, Successful: {successful_count}, Failed: {failed_count}")
    if all_scraped_data:
        try:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(all_scraped_data, f, ensure_ascii=False, indent=4)
            logging.info(f"Successfully saved {successful_count} scraped texts to {OUTPUT_FILE}")
        except Exception as e:
            logging.error(f"Error saving data to JSON file {OUTPUT_FILE}: {e}")
    else:
        logging.warning("No data was successfully scraped.")
    logging.info("Scraper script finished.")
