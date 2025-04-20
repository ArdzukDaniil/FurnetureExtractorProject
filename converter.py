import json
import re
import os
import string

# --- Конфигурация ---
INPUT_JSON_FILE = "data/raw_texts/scraped_texts.json"  # Имя вашего исходного файла
OUTPUT_JSON_FILE = "data/annotated/spacy_training_data.json"
LABEL = "PRODUCT"


# Ключевые слова - ЯКОРЯ (более строгий список основных типов)
# Мы не будем размечать их сами по себе, а будем искать названия ВОКРУГ них
PRODUCT_ANCHORS = list(
    set(
        [
            "sofa",
            "sofas",
            "couch",
            "couches",
            "loveseat",
            "sectional",
            "chair",
            "chairs",
            "armchair",
            "stool",
            "stools",
            "barstool",
            "bench",
            "benches",
            "ottoman",
            "footstool",
            "table",
            "tables",
            "dining table",
            "coffee table",
            "side table",
            "end table",
            "console",
            "console table",
            "desk",
            "desks",
            "bed",
            "beds",
            "daybed",
            "bunk bed",
            "bed frame",
            "headboard",
            "footboard",
            "mattress",
            "mattresses",
            "dresser",
            "dressers",
            "chest",
            "chest of drawers",
            "nightstand",
            "bedside table",
            "sideboard",
            "buffet",
            "cabinet",
            "cabinets",
            "bookcase",
            "bookshelf",
            "shelf",
            "shelves",
            "shelving",
            "tv unit",
            "media unit",
            "media console",
            "entertainment center",
            "wardrobe",
            "armoire",
            "closet",
            "hammock",
            "hammocks",
            "planter",
            "planters",
            "plant stand",
            "mirror",
            "mirrors",
            "vanity",
            "vanities",
            "lamp",
            "lamps",
            "light",
            "lighting",
            "pendant",
            "chandelier",
            "sconce",
            "rug",
            "rugs",
            "swing",
            "swings",
            "umbrella",
            "umbrellas",
            "topper",  # Из примера "Mattress Protector Topper"
            "protector",  # Из примера "Mattress Protector"
        ]
    )
)
PRODUCT_ANCHORS.sort(key=len, reverse=True)

# Исключения - слова, которые ТОЧНО не являются частью названия продукта
# или служат сигналом конца названия
EXCLUSION_KEYWORDS = set(
    [
        # UI & Навигация
        "home",
        "shop",
        "products",
        "collections",
        "category",
        "categories",
        "all",
        "view all",
        "search",
        "filter",
        "sort by",
        "refine by",
        "grid",
        "list",
        "account",
        "login",
        "log in",
        "register",
        "sign up",
        "sign in",
        "logout",
        "cart",
        "basket",
        "checkout",
        "add to cart",
        "view cart",
        "continue shopping",
        "shopping",
        "wishlist",
        "add to wishlist",
        "quick view",
        "view",
        "share",
        "tweet",
        "pin it",
        "facebook",
        "twitter",
        "pinterest",
        "instagram",
        "youtube",
        "google",
        "next",
        "previous",
        "page",
        "show more",
        "load more",
        "back",
        "go to",
        "more results",
        "menu",
        "close",
        "skip",
        "content",
        "zoom",
        "expand",
        "esc",
        "select",
        "choose",
        "change",
        "request",
        "contact",
        "email",
        "phone",
        "chat",
        "call",
        "send",
        "message",
        "subscribe",
        "newsletter",
        "mailing list",
        # Информация и Сервис
        "about us",
        "our story",
        "contact us",
        "customer service",
        "support",
        "help",
        "faq",
        "faqs",
        "need help",
        "shipping",
        "delivery",
        "free shipping",
        "dispatch",
        "returns",
        "refunds",
        "policy",
        "policies",
        "terms",
        "service",
        "privacy",
        "warranty",
        "guarantee",
        "plan",
        "protection",
        "guardsman",
        "track my order",
        "order",
        "orders",
        "purchase",
        "payment",
        "payments",
        "financing",
        "pay",
        "emi",
        "afterpay",
        "klarna",
        "zip",
        "paypal",
        "reviews",
        "review",
        "testimonials",
        "customer reviews",
        "write a review",
        "rating",
        "ratings",
        "stars",
        "based on",
        "verified buyer",
        "details",
        "description",
        "specifications",
        "technical details",
        "features",
        "key features",
        "product details",
        "product info",
        "information",
        "dimensions",
        "size",
        "width",
        "depth",
        "height",
        "length",
        "weight",
        "cm",
        "inches",
        "kg",
        "lbs",
        "diam",
        "materials",
        "material",
        "upholstery",
        "construction",
        "care",
        "maintenance",
        "cleaning",
        "color",
        "colour",
        "finish",
        "styles",
        "style",
        "design",
        "designer",
        "brand",
        "vendor",
        "manufacturer",
        "collection",
        "range",
        "assembly",
        "installation",
        "instructions",
        "guide",
        "how to",
        # Цены и Скидки
        "price",
        "regular price",
        "sale price",
        "unit price",
        "total price",
        "save",
        "off",
        "discount",
        "sale",
        "clearance",
        "offers",
        "promotion",
        "promotions",
        "deal",
        "deals",
        "bundle",
        "rrp",
        "was",
        "now",
        "from",
        "usd",
        "eur",
        "gbp",
        "aud",
        "cad",
        "sgd",
        "sek",
        "nzd",
        "inr",
        "php",
        "zar",
        "dkk",
        "hkd",
        "myr",
        # Валюты и символы
        "tax",
        "vat",
        "gst",
        "inclusive",
        "exclusive",
        # Общие слова и фразы
        "and",
        "or",
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "as",
        "of",
        "from",
        "our",
        "your",
        "you",
        "we",
        "us",
        "it",
        "its",
        "they",
        "them",
        "this",
        "that",
        "these",
        "those",
        "new",
        "arrivals",
        "featured",
        "related",
        "recommended",
        "popular",
        "best",
        "sellers",
        "also",
        "more",
        "other",
        "available",
        "in stock",
        "out of stock",
        "sold out",
        "backordered",
        "unavailable",
        "limited",
        "ready",
        "only",
        "accessories",
        "decor",
        "homewares",
        "textiles",
        "gifts",  # Общие категории
        "storage",  # Слишком общее
        "outdoor",
        "indoor",  # Расположение
        "set",
        "pcs",  # Часто не сам продукт
        "queen",
        "king",
        "twin",
        "cal",
        "california",
        "single",
        "double",  # Размеры, если отдельно
        "left",
        "right",
        "hand",
        "facing",  # Направления
        "plus",
        "complete",
        "gift card",
        "gift cards",
        "gift voucher",
        "gift vouchers",
        "membership",
        "card",  # Не физические товары
        "bulb",
        "bulbs",  # Компоненты
        "information",
        "news",
        "journal",
        "blog",
        "articles",
        "text",
        "image",
        "images",
        "video",
        "gallery",
        "day",
        "days",
        "week",
        "weeks",
        "month",
        "months",
        "year",
        "years",  # Время
        "true",
        "false",  # Булевы значения
        "llc",
        "inc",
        "ltd",
        "co",
        "gmbh",
        "srl",  # Суффиксы компаний
        "est",
        "aedt",
        "gmt",  # Часовые пояса
        "sku",
        "id",
        "qty",
        "n/a",
        "ref",
        "loading",
        "refresh",
        "tap",
        "click",
        "esc",
        "slide",
        "toggle",
        "swatches",
        "options",
        "variant",
        "am",
        "pm",
        "no",
        "yes",
        "ok",
        "all",
        "good",
        "great",
        "nice",
        "beautiful",
        "quality",
        "comfy",
        "perfect",
        "love",
        # Оценочные слова из отзывов
        "item",
        "items",  # Слишком общее
        "furniture",  # Слишком общая категория
        "via",
        "http",
        "https",
        "www",
        "com",
        "co",
        "uk",
        "au",
        "org",  # Части URL или email
        "note",
        "please",
        "read",
        "see",
        "find",
        "check",
        "visit",
        "click",
        "get",
        "buy",
        "shop",  # Глаголы и призывы
        "what",
        "how",
        "why",  # Вопросительные слова
        # Очень короткие слова, которые вряд ли будут названиями сами по себе
        "be",
        "do",
        "go",
        "me",
        "my",
        "of",
        "on",
        "or",
        "so",
        "to",
        "up",
        "us",
        # Знаки препинания (некоторые обрабатываются отдельно, но добавим сюда для надежности)
        ",",
        ".",
        ":",
        ";",
        "?",
        "!",
        "|",
        "/",
        "\\",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "<",
        ">",
        "=",
        "+",
        "*",
        "%",
        "#",
        "@",
        # Специфичный мусор
        "frequently",
        "bought",
        "together",
        "recently",
        "viewed",
        "customers",
        "also",
        "need",
        "to",
        "know",
        "use",
        "collapsible",
        "tabs",
        "detailed",
        "help",
        "make",
        "purchasing",
        "decision",
        "ex",
        "share",
        "on",
        "facebook",
        "tweet",
        "on",
        "x",
        "pin",
        "it",
        "on",
        "pinterest",
        "error",
        "liquid",
        "snippet",
        "asset",
        "icon",
        "could",
        "not",
        "be",
        "found",
        "translation",
        "missing",
        "en",
        "general",
        "accessibility",
        "label",
        "compare_at_price",
        "selling_plan_allocations",
        "quantity_rule",
        "min",
        "max",
        "increment",
        "json",
        "null",
        "true",
        "false",
        "copyright",
        "reserved",
        "rights",
        "powered",
        "shopify",
        "continue",
        "apply",
        "cancel",
        "confirm",
        "save",
        "edit",
        "delete",
        "remove",
        # Добавим еще стоп-слов
        "all",
        "just",
        "being",
        "over",
        "both",
        "through",
        "yourselves",
        "its",
        "before",
        "herself",
        "had",
        "should",
        "to",
        "only",
        "under",
        "ours",
        "has",
        "do",
        "them",
        "his",
        "very",
        "they",
        "not",
        "during",
        "now",
        "him",
        "nor",
        "did",
        "this",
        "she",
        "each",
        "further",
        "where",
        "few",
        "because",
        "doing",
        "some",
        "are",
        "our",
        "ourselves",
        "out",
        "what",
        "for",
        "while",
        "does",
        "above",
        "between",
        "be",
        "we",
        "who",
        "were",
        "here",
        "hers",
        "by",
        "on",
        "about",
        "of",
        "against",
        "or",
        "own",
        "into",
        "yourself",
        "down",
        "might",
        "will",
        "your",
        "from",
        "her",
        "whom",
        "there",
        "been",
        "would",
        "these",
        "up",
        "is",
        "other",
        "in",
        "such",
        "off",
        "i",
        "am",
        "have",
        "with",
        "than",
        "he",
        "me",
        "myself",
        "which",
        "below",
        "can",
        "after",
        "if",
        "again",
        "no",
        "when",
        "same",
        "any",
        "how",
        "other",
        "that",
        "many",
        "shan",
        "a",
        "an",
        "the",
        "and",
        "but",
        "if",
        "or",
        "because",
        "as",
        "until",
        "while",
        "of",
        "at",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "from",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "any",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
    ]
)


# --- Функции ---


def load_data(filepath):
    """Загружает JSON данные из файла."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Ошибка: Файл '{filepath}' не найден.")
        return None
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось декодировать JSON из файла '{filepath}'.")
        return None
    except Exception as e:
        print(f"Произошла ошибка при чтении файла '{filepath}': {e}")
        return None


def save_data(filepath, data):
    """Сохраняет данные в JSON файл."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Данные успешно сохранены в '{filepath}'")
    except Exception as e:
        print(f"Произошла ошибка при сохранении файла '{filepath}': {e}")


def get_potential_spans(text, anchors, exclusions):
    """Находит потенциальные полные названия продуктов."""
    potential_entities = []
    text_lower = text.lower()

    # Разделим текст на строки для контекстного анализа
    lines = text.split("\n")
    line_starts = [0] * len(lines)
    current_pos = 0
    for i, line in enumerate(lines):
        line_starts[i] = current_pos
        current_pos += len(line) + 1  # +1 за '\n'

    # Ищем якоря
    anchor_matches = []
    for anchor in anchors:
        anchor_lower = anchor.lower()
        try:
            # Ищем якорь как отдельное слово
            pattern = r"\b" + re.escape(anchor_lower) + r"\b"
            for match in re.finditer(pattern, text_lower):
                anchor_matches.append(
                    {"start": match.start(), "end": match.end(), "keyword": anchor}
                )
        except re.error as e:
            print(f"Ошибка regex для якоря '{anchor}': {e}")
            continue

    if not anchor_matches:
        return []

    # Сортируем якоря по позиции
    anchor_matches.sort(key=lambda x: x["start"])

    # Пытаемся найти полные названия вокруг якорей
    processed_spans = set()

    for match in anchor_matches:
        start, end = match["start"], match["end"]

        # Пропускаем, если этот якорь уже часть обработанного спана
        if any(
            start >= ps_start and end <= ps_end for ps_start, ps_end in processed_spans
        ):
            continue

        # --- Эвристика для поиска границ ---

        # Ищем начало строки, в которой найден якорь
        line_index = -1
        for i in range(len(line_starts)):
            if start >= line_starts[i]:
                line_index = i
            else:
                break

        current_line_start = line_starts[line_index] if line_index != -1 else 0
        current_line_end = (
            line_starts[line_index + 1] - 1
            if line_index < len(lines) - 1
            else len(text)
        )
        current_line = text[current_line_start:current_line_end].strip()

        # Потенциальное Начало: Ищем назад от якоря до начала строки или стоп-слова/пунктуации
        potential_start = start
        while potential_start > current_line_start:
            char_before = text[potential_start - 1]
            # Ищем первое слово слева
            match_word_before = list(re.finditer(r"\b\w+\b", text[:potential_start]))
            if not match_word_before:
                break  # Нет слов слева в строке

            last_word_span = match_word_before[-1].span()
            last_word = text[last_word_span[0] : last_word_span[1]]

            # Условия остановки поиска НАЗАД:
            # 1. Слово является исключением ИЛИ начинается с маленькой буквы (и не число) ИЛИ это пунктуация
            # 2. Достигли начала строки
            if (
                last_word.lower() in exclusions
                or (last_word[0].islower() and not last_word.isdigit())
                or last_word in string.punctuation
            ):
                break

            # Если слово подходит, сдвигаем начало
            potential_start = last_word_span[0]
            # Пропускаем пробелы перед словом
            while (
                potential_start > current_line_start
                and text[potential_start - 1].isspace()
            ):
                potential_start -= 1

        # Потенциальный Конец: Ищем вперед от якоря до конца строки или стоп-слова/цены/пунктуации
        potential_end = end
        while potential_end < current_line_end:
            char_after = text[potential_end] if potential_end < len(text) else ""
            # Ищем первое слово справа
            match_word_after = re.search(r"\b\w+\b", text[potential_end:])
            if not match_word_after:
                break  # Нет слов справа

            next_word_span_rel = match_word_after.span()
            next_word_span_abs = (
                potential_end + next_word_span_rel[0],
                potential_end + next_word_span_rel[1],
            )
            next_word = text[next_word_span_abs[0] : next_word_span_abs[1]]

            # Ищем признаки цены или кнопки "Add to Cart" после слова
            text_after_word = text[
                next_word_span_abs[1] : min(next_word_span_abs[1] + 30, len(text))
            ]  # Смотрим немного вперед
            price_pattern = r"(\$|€|£|₹|kr|rm|php|zar|sgd|aud|cad|nzd)\s?[\d,.]+"
            # Добавим "add to cart", "view product", "choose options" как сигналы конца
            end_signals = [
                "add to cart",
                "view product",
                "choose options",
                "regular price",
                "sale price",
                "unit price",
                "save",
            ]

            # Условия остановки поиска ВПЕРЕД:
            # 1. Слово является исключением ИЛИ начинается с маленькой буквы (и не число/размер типа king/queen)
            # 2. После слова идет цена или сигнал конца
            # 3. Достигли конца строки / текста
            # 4. Встретили два переноса строки подряд (вероятно, конец блока)
            if (
                next_word.lower() in exclusions
                or (
                    next_word[0].islower()
                    and not next_word.isdigit()
                    and next_word.lower()
                    not in [
                        "king",
                        "queen",
                        "single",
                        "double",
                        "black",
                        "white",
                        "grey",
                        "blue",
                        "red",
                        "green",
                        "brown",
                        "ash",
                        "oak",
                        "walnut",
                        "metal",
                        "leather",
                        "fabric",
                        "timber",
                        "rattan",
                    ]
                )  # Разрешаем некоторые атрибуты
                or re.search(price_pattern, text_after_word, re.IGNORECASE)
                or any(signal in text_after_word.lower() for signal in end_signals)
                or "\n\n"
                in text[
                    potential_end : next_word_span_abs[0] + 1
                ]  # Два переноса строки
            ):
                break

            # Если слово подходит, сдвигаем конец
            potential_end = next_word_span_abs[1]

        # --- Фильтрация и добавление кандидата ---
        final_start = potential_start
        final_end = potential_end
        final_span = (final_start, final_end)
        final_text = text[final_start:final_end].strip()

        # Удаляем висячие знаки препинания в начале/конце
        while final_text and final_text[0] in string.punctuation + " ":
            final_text = final_text[1:]
            final_start += 1
        while final_text and final_text[-1] in string.punctuation + " ":
            final_text = final_text[:-1]
            final_end -= 1

        final_span = (final_start, final_end)  # Обновляем спан

        # Дополнительные проверки:
        # - Не слишком короткий (< 3 символов)
        # - Не совпадает точно с якорем (если только якорь не длинный и с большой буквы)
        # - Не совпадает точно с исключением
        # - Не состоит только из цифр или пунктуации
        # - Содержит хотя бы одну букву
        is_valid = True
        if (final_end - final_start) < 3:
            is_valid = False
        if (
            final_text.lower() == match["keyword"].lower()
            and not match["keyword"][0].isupper()
            and len(match["keyword"]) < 5
        ):
            is_valid = False
        if final_text.lower() in exclusions:
            is_valid = False
        if final_text.isdigit() or all(
            c in string.punctuation + " " for c in final_text
        ):
            is_valid = False
        if not re.search(r"[a-zA-Z]", final_text):
            is_valid = False

        # Проверка на перекрытие перед добавлением
        overlapped = False
        for ps_start, ps_end, _ in potential_entities:
            if max(final_start, ps_start) < min(final_end, ps_end):
                # Если новая сущность длиннее, она может заменить старую
                if (final_end - final_start) > (ps_end - ps_start):
                    continue  # Позволим добавить, разберемся на следующем шаге
                else:
                    overlapped = True
                    break

        if is_valid and not overlapped:
            potential_entities.append(
                [final_start, final_end, final_text]
            )  # Сохраняем текст для разрешения конфликтов
            processed_spans.add(final_span)

    # --- Разрешение конфликтов перекрытий (приоритет длинным) ---
    if not potential_entities:
        return []

    # Сортируем: сначала по началу, потом по длине (убывание)
    potential_entities.sort(key=lambda x: (x[0], -(x[1] - x[0])))

    final_entities = []
    covered_indices = set()

    for start, end, ent_text in potential_entities:
        # Проверяем, не перекрывается ли *значительно* с уже добавленными
        if any(i in covered_indices for i in range(start, end)):
            continue  # Пропускаем, если уже занято

        # Проверяем, не является ли сущность просто одним словом-исключением
        # (На случай, если фильтрация выше пропустила)
        if ent_text.lower() in exclusions and len(ent_text.split()) == 1:
            continue

        final_entities.append([start, end, LABEL])
        covered_indices.update(range(start, end))

    # Сортируем по начальной позиции для spaCy
    final_entities.sort(key=lambda x: x[0])

    return final_entities


# --- Основной код ---
if __name__ == "__main__":
    # Создаем dummy input_data.json, если его нет, для тестирования
    if not os.path.exists(INPUT_JSON_FILE):
        print(f"Файл {INPUT_JSON_FILE} не найден. Создаю пример файла для теста.")
        dummy_data = [
            {
                "url": "http://example.com/1",
                "text": "Beautiful blue sofa for sale. Also a nice dining table.",
            },
            {
                "url": "http://example.com/2",
                "text": "Check out our new beds and mattresses. Gift cards available!",
            },
            {
                "url": "http://example.com/3",
                "text": "This wooden side table is lovely. Buy the Hamar Plant Stand - Ash now! Regular price $515",
            },
        ]
        save_data(INPUT_JSON_FILE, dummy_data)

    input_records = load_data(INPUT_JSON_FILE)

    if input_records:
        spacy_training_data = []
        print(
            f"Начинаю обработку {len(input_records)} записей для метки '{LABEL}' (v2)..."
        )
        not_found_count = 0

        for i, record in enumerate(input_records):
            text = record.get("text")
            if not text or not isinstance(text, str):
                continue

            entities = get_potential_spans(text, PRODUCT_ANCHORS, EXCLUSION_KEYWORDS)

            if entities:
                spacy_training_data.append({"text": text, "entities": entities})
            else:
                not_found_count += 1

            if (i + 1) % 50 == 0:  # Выводим прогресс каждые 50 записей
                print(f"Обработано {i + 1}/{len(input_records)} записей...")

        print(f"Обработка завершена.")
        print(
            f"Найдено потенциальных сущностей '{LABEL}' в {len(spacy_training_data)} записях."
        )
        print(f"Не найдено сущностей в {not_found_count} записях.")

        save_data(OUTPUT_JSON_FILE, spacy_training_data)

        # Выведем пример первых нескольких размеченных записей
        print(f"\nПример первых 5 размеченных записей (файл: {OUTPUT_JSON_FILE}):")
        for item in spacy_training_data[:5]:
            print(json.dumps(item, ensure_ascii=False, indent=2))
            print("-" * 20)

        # Пример для записи №1 (индекс 0 в вашем JSON)
        print("\nПример разметки для записи #1 (Euro Top Mattress King):")
        if len(input_records) > 0 and input_records[0].get("text"):
            record1_text = input_records[0]["text"]
            record1_entities = get_potential_spans(
                record1_text, PRODUCT_ANCHORS, EXCLUSION_KEYWORDS
            )
            print(
                json.dumps(
                    {"text": record1_text[:500] + "...", "entities": record1_entities},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print("Не удалось обработать запись #1 для примера.")

    else:
        print("Не удалось загрузить входные данные.")
