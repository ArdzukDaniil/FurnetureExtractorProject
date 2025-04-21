import requests
from bs4 import BeautifulSoup
from django.apps import apps
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'


def extract_text_from_html(html_content: str) -> Optional[str]:
    """Извлекает основной текст из HTML (аналогично scraper.py)."""
    if not html_content:
        return None
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'form', 'link', 'meta']):
            tag.decompose()

        main_content = soup.find('main') or soup.find('article') or soup.body
        if main_content:
            text = main_content.get_text(separator=' ', strip=True)
            cleaned_text = ' '.join(text.split())
            return cleaned_text if len(cleaned_text) > 50 else None
        else:
            return None
    except Exception as e:
        logger.error(f"Error parsing HTML: {e}", exc_info=True)
        return None


def scrape_and_extract_text(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Скачивает URL, извлекает текст.
    Возвращает (текст, сообщение_об_ошибке)
    """
    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        content_type = response.headers.get('content-type', '').lower()
        if 'html' not in content_type:
            logger.warning(f"Content-Type is not HTML for {url}: {content_type}")
            return None, f"URL content type is not HTML ({content_type})."

        html_content = response.text
        logger.info(f"Successfully fetched URL: {url}")

        extracted_text = extract_text_from_html(html_content)
        if extracted_text:
            return extracted_text, None
        else:
            logger.warning(f"No meaningful text extracted from URL: {url}")
            return None, "Could not extract meaningful text from the page."

    except requests.exceptions.Timeout:
        logger.warning(f"Request timed out for URL: {url}")
        return None, "The request timed out."
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP Error for URL {url}: {e.response.status_code}")
        return None, f"Could not fetch URL (HTTP {e.response.status_code})."
    except requests.exceptions.RequestException as e:
        logger.error(f"Could not fetch or process URL: {url}. Error: {e}", exc_info=True)
        return None, f"Could not fetch URL: {e}"
    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping {url}: {e}", exc_info=True)
        return None, "An unexpected error occurred during scraping."


def extract_products_with_ner(text: str) -> List[str]:
    """Обрабатывает текст с помощью загруженной NER модели."""
    products = []
    # Получаем доступ к загруженной модели через AppConfig
    extractor_config = apps.get_app_config('extractor')
    nlp = extractor_config.nlp_model

    if nlp is None:
        logger.error("NER model is not loaded. Cannot extract products.")

        return []

    if not text:
        return []

    try:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == 'PRODUCT':
                products.append(ent.text.strip())

        products = list(dict.fromkeys(products))
        logger.info(f"Found {len(products)} potential products.")
    except Exception as e:
        logger.error(f"Error during NER processing: {e}", exc_info=True)

        return []

    return products
