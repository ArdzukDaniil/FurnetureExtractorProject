import requests
from bs4 import BeautifulSoup
import json
import os
import logging
import time
from typing import List, Dict, Optional, Tuple

# --- Конфигурация ---
URL_LIST_FILE = "../data/urls.txt"  # Файл со списком URL (положи его рядом со скриптом)
OUTPUT_DIR = os.path.join("../data", "raw_texts")  # Папка для сохранения результатов
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "scraped_texts.json")  # Имя файла с результатами
NUM_URLS_TO_PROCESS = 500  # Сколько URL из списка пытаемся обработать (с запасом)
TARGET_SUCCESSFUL_PAGES = 150  # Целевое количество успешно собранных страниц
REQUEST_TIMEOUT = 20  # Таймаут для HTTP запроса в секундах
SLEEP_INTERVAL = 1  # Пауза между запросами в секундах (чтобы не банили)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"  # Пример User-Agent

# --- Настройка Логирования ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Функции ---


def load_urls(filepath: str) -> List[str]:
    """Загружает список URL из файла, удаляя пустые строки."""
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
    """
    Извлекает основной текст из HTML, удаляя ненужные теги.
    Старается найти теги <main> или <article>, иначе использует <body>.
    """
    if not html_content:
        return None
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Удалить ненужные теги, которые обычно не содержат основного контента товара
        for tag in soup(
            [
                "script",
                "style",
                "nav",
                "header",
                "footer",
                "aside",
                "form",
                "link",
                "meta",
            ]
        ):
            tag.decompose()

        # Попробовать найти основной контент
        main_content = soup.find("main")
        if not main_content:
            main_content = soup.find("article")
        # Добавим еще несколько общих контейнеров, если <main> и <article> не найдены
        if not main_content:
            common_containers = [
                "#content",
                "#main-content",
                ".content",
                ".main",
                ".product-details",
            ]  # Примеры селекторов
            for selector in common_containers:
                main_content = soup.select_one(selector)
                if main_content:
                    break
        # Если ничего специфичного не найдено, взять весь body
        if not main_content:
            main_content = soup.body

        if main_content:
            # Получаем текст, используя пробел как разделитель, убираем лишние пробелы в начале/конце
            text = main_content.get_text(separator=" ", strip=True)
            # Заменяем множественные пробелы и переносы строк на один пробел
            cleaned_text = " ".join(text.split())
            if (
                len(cleaned_text) > 50
            ):  # Простая проверка, что извлекли не просто пару слов
                return cleaned_text
            else:
                logging.warning(
                    "Extracted text seems too short, might be non-content page."
                )
                # Можно вернуть и короткий текст, но лучше None, если он явно не контентный
                # Если главные блоки не дали текста, попробуем весь soup, но это шумнее
                full_text = soup.get_text(separator=" ", strip=True)
                cleaned_full_text = " ".join(full_text.split())
                if len(cleaned_full_text) > 50:
                    logging.warning("Falling back to full soup text extraction.")
                    return cleaned_full_text
                else:
                    return None  # Если и полный текст короткий, то точно пусто
        else:
            logging.warning("Could not find main content or body tag.")
            return None  # Если не нашли даже body

    except Exception as e:
        logging.error(f"Error parsing HTML: {e}")
        return None


def scrape_url(url: str) -> Optional[Dict[str, str]]:
    """
    Скачивает HTML с URL, извлекает текст и возвращает словарь или None при ошибке.
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        # Проверяем статус ответа (2xx означает успех)
        response.raise_for_status()

        # Проверяем тип контента, чтобы случайно не парсить картинки или PDF
        content_type = response.headers.get("content-type", "").lower()
        if "html" not in content_type:
            logging.warning(
                f"Skipping URL {url} - Content-Type is not HTML ({content_type})"
            )
            return None

        html_content = response.text
        logging.info(f"Successfully fetched URL: {url}")

        # Извлекаем текст
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
        logging.warning(
            f"HTTP Error for URL {url}: {e.response.status_code} {e.response.reason}"
        )
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not fetch or process URL: {url}. Error: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while processing {url}: {e}")
        return None


# --- Основной блок выполнения ---
if __name__ == "__main__":
    logging.info("Starting scraper script...")

    # Создаем папку для вывода, если её нет
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logging.info(f"Output directory set to: {OUTPUT_DIR}")

    # Загружаем URL
    urls_to_scrape = load_urls(URL_LIST_FILE)

    if not urls_to_scrape:
        logging.info("No URLs to process. Exiting.")
        exit()

    # Основной цикл сбора данных
    all_scraped_data: List[Dict[str, str]] = []
    processed_count = 0
    successful_count = 0
    failed_count = 0

    logging.info(
        f"Attempting to scrape up to {NUM_URLS_TO_PROCESS} URLs to get {TARGET_SUCCESSFUL_PAGES} successful pages."
    )

    for i, url in enumerate(urls_to_scrape):
        if processed_count >= NUM_URLS_TO_PROCESS:
            logging.info(f"Reached processing limit of {NUM_URLS_TO_PROCESS} URLs.")
            break
        if successful_count >= TARGET_SUCCESSFUL_PAGES:
            logging.info(
                f"Reached target of {TARGET_SUCCESSFUL_PAGES} successfully scraped pages."
            )
            break

        logging.info(f"Processing URL {i+1}/{len(urls_to_scrape)}: {url}")
        processed_count += 1
        result = scrape_url(url)

        if result:
            all_scraped_data.append(result)
            successful_count += 1
            logging.info(
                f"Success! Pages collected: {successful_count}/{TARGET_SUCCESSFUL_PAGES}"
            )
        else:
            failed_count += 1

        # Пауза между запросами
        if i < len(urls_to_scrape) - 1:  # Не спать после последнего URL
            logging.info(f"Sleeping for {SLEEP_INTERVAL} second(s)...")
            time.sleep(SLEEP_INTERVAL)

    # Сохранение результатов в JSON
    logging.info(
        f"Scraping finished. Total URLs processed: {processed_count}, Successful: {successful_count}, Failed: {failed_count}"
    )
    if all_scraped_data:
        try:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(all_scraped_data, f, ensure_ascii=False, indent=4)
            logging.info(
                f"Successfully saved {successful_count} scraped texts to {OUTPUT_FILE}"
            )
        except Exception as e:
            logging.error(f"Error saving data to JSON file {OUTPUT_FILE}: {e}")
    else:
        logging.warning("No data was successfully scraped.")

    logging.info("Scraper script finished.")
