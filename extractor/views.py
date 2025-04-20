# extractor/views.py
from django.shortcuts import render
from django.http import HttpRequest # Убрали JsonResponse, HttpResponseBadRequest, require_http_methods, csrf_exempt, json, если они больше не нужны (а они не нужны без API)
from .services import scrape_and_extract_text, extract_products_with_ner
import logging

logger = logging.getLogger(__name__)

# --- НОВАЯ VIEW для обработки HTML формы (остается без изменений) ---
def home_view(request: HttpRequest):
    """
    View для главной страницы: отображает форму и обрабатывает ее отправку.
    """
    context = {} # Контекст для передачи данных в шаблон

    if request.method == 'POST':
        url = request.POST.get('url', '').strip()
        context['submitted_url'] = url # Сохраняем URL для отображения в форме

        if not url:
            context['error'] = "Please enter a URL."
            # Простая проверка на наличие http/https - базовая валидация URL
            # Для надежности можно использовать regex или Django Forms
        elif not url.startswith('http://') and not url.startswith('https://'):
             context['error'] = "Please enter a valid URL (starting with http:// or https://)."
        else:
            # --- Выполняем логику экстракции (как в API view) ---
            logger.info(f"Processing URL from form: {url}")
            text, scrape_error = scrape_and_extract_text(url)

            if scrape_error:
                logger.warning(f"Scraping failed for {url}: {scrape_error}")
                context['error'] = f"Failed to process URL: {scrape_error}"
            elif not text:
                logger.warning(f"No text could be extracted from {url} after successful fetch.")
                context['message'] = 'Successfully processed URL, but no relevant text containing product names was found.'
                context['products'] = [] # Пустой список
            else:
                # Ошибка модели должна логироваться в services
                products = extract_products_with_ner(text)
                logger.info(f"Found {len(products)} products for URL: {url}")
                context['products'] = products
                if not products:
                     context['message'] = 'Successfully processed URL, but no product names were identified by the NER model.'

        return render(request, 'extractor/index.html', context)

    # Если GET запрос, просто отображаем страницу
    return render(request, 'extractor/index.html', context)

