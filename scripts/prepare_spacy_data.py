import json
import spacy
from spacy.tokens import DocBin, Span
import random
import os
from sklearn.model_selection import train_test_split  # Для удобного разделения

# --- Конфигурация ---
# Путь к JSON файлу, экспортированному из Label Studio
# Предполагается формат: [{"text": "...", "entities": [[start, end, "LABEL"], ...]}, ...]
LABEL_STUDIO_EXPORT_FILE = os.path.join(
    "../data", "annotated", "spacy_training_data.json"
)  # !!! ЗАМЕНИ НА ИМЯ ТВОЕГО ФАЙЛА !!!

# Папка для сохранения готовых данных для spaCy
OUTPUT_DIR = os.path.join("../data", "spacy_data")

# Имена выходных файлов
TRAIN_DATA_FILE = os.path.join(OUTPUT_DIR, "train.spacy")
DEV_DATA_FILE = os.path.join(OUTPUT_DIR, "dev.spacy")

# Доля данных для валидации (например, 0.2 = 20%)
DEV_SPLIT = 0.2

# Имя метки, которую мы размечали
TARGET_LABEL = "PRODUCT"

# Базовая модель spaCy (нужна для токенизации при создании Doc)
# Используем пустую модель 'en', так как нам нужна только токенизация
NLP_MODEL = "en_core_web_sm"  # или "en_core_web_md" / "lg" если установлены
# Или можно использовать пустую: spacy.blank("en") - быстрее, но токенизация может быть чуть хуже
# nlp = spacy.blank("en")
try:
    nlp = spacy.load(NLP_MODEL)
    print(f"Loaded spaCy model '{NLP_MODEL}' for tokenization.")
except OSError:
    print(f"spaCy model '{NLP_MODEL}' not found. Trying blank 'en' model.")
    nlp = spacy.blank("en")
    print(
        "Using blank 'en' model. Consider downloading a pretrained model for better tokenization: python -m spacy download en_core_web_sm"
    )


# --- Функции ---


def load_label_studio_data(filepath: str) -> list:
    """Загружает данные из JSON, экспортированного из Label Studio."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Loaded {len(data)} records from {filepath}")
        # Проверка формата первого элемента (опционально)
        if data and isinstance(data, list) and isinstance(data[0], dict):
            print("Data seems to be in the expected list-of-dictionaries format.")
        elif data:
            print(
                "Warning: Data format might differ from expected list-of-dictionaries."
            )
        return data
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {filepath}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred while loading data: {e}")
        return []


def convert_to_spacy_format(data: list) -> list:
    """
    Преобразует данные из формата Label Studio (как в примере пользователя)
    в формат списка кортежей spaCy: [(text, {"entities": [(start, end, label), ...]})].
    """
    spacy_data = []
    skipped_count = 0
    for record in data:
        text = record.get("text")
        entities = record.get(
            "entities"
        )  # Ожидаем список списков: [[start, end, label], ...]

        if not text or not isinstance(text, str):
            print(f"Warning: Skipping record due to missing or invalid text: {record}")
            skipped_count += 1
            continue

        formatted_entities = []
        if isinstance(entities, list):
            for ent in entities:
                # Проверяем, что это список и в нем 3 элемента
                if isinstance(ent, list) and len(ent) == 3:
                    start, end, label = ent
                    # Проверяем типы и метку
                    if (
                        isinstance(start, int)
                        and isinstance(end, int)
                        and isinstance(label, str)
                    ):
                        if label == TARGET_LABEL:
                            # Проверка корректности индексов относительно текста
                            if 0 <= start < len(text) and start < end <= len(text):
                                formatted_entities.append((start, end, label))
                            else:
                                print(
                                    f"Warning: Skipping invalid entity indices {ent} for text snippet: '{text[:50]}...'"
                                )
                        # else: # Игнорируем другие метки, если они есть
                        #    print(f"Skipping entity with non-target label: {label}")
                    else:
                        print(f"Warning: Skipping entity with invalid types: {ent}")
                else:
                    print(f"Warning: Skipping malformed entity entry: {ent}")
        elif entities is not None:  # Если entities есть, но это не список
            print(f"Warning: 'entities' field is not a list in record: {record}")

        # Добавляем в результат только если есть текст
        # (даже если нет сущностей - это негативный пример, полезный для обучения)
        spacy_data.append((text, {"entities": formatted_entities}))

    if skipped_count > 0:
        print(f"Skipped {skipped_count} records due to missing/invalid text.")
    print(f"Converted {len(spacy_data)} records to spaCy format.")
    return spacy_data


def create_docbin(data: list, output_file: str):
    """Создает и сохраняет DocBin из данных в формате spaCy."""
    db = DocBin()
    skipped_spans = 0
    total_spans = 0

    for text, annotations in data:
        doc = nlp.make_doc(text)  # Создаем Doc объект
        ents = []
        entity_indices = annotations.get("entities", [])
        total_spans += len(entity_indices)

        for start, end, label in entity_indices:
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is None:
                print(
                    f"Warning: Skipping entity span [{start}, {end}, {label}] for text: '{text[start-10:end+10]}...' (Could not form span)"
                )
                skipped_spans += 1
            else:
                ents.append(span)

        # Попытка установить сущности. Обработка перекрывающихся спанов.
        try:
            doc.ents = ents
        except ValueError as e:
            # Часто бывает из-за перекрывающихся спанов - spaCy их не любит по умолчанию
            print(
                f"Warning: Could not set entities for doc (possibly overlapping spans?): {e}"
            )
            # Можно попробовать отфильтровать перекрывающиеся или просто пропустить
            # Простейший вариант - пропустить установку ents для этого документа
            # doc.ents = [] # Сбросить, если не удалось установить
            print(f"Text snippet: {text[:100]}...")
            print(
                f"Problematic ents: {[(e.start_char, e.end_char, e.label_) for e in ents]}"
            )

        db.add(doc)  # Добавляем Doc в DocBin

    db.to_disk(output_file)  # Сохраняем DocBin на диск
    print(f"Saved {len(data)} documents to {output_file}")
    if skipped_spans > 0:
        print(
            f"Skipped {skipped_spans}/{total_spans} entity spans due to alignment issues."
        )
    if skipped_spans == total_spans and total_spans > 0:
        print(
            "ERROR: All entity spans were skipped. Check your annotation indices and text processing."
        )


# --- Основной блок выполнения ---
if __name__ == "__main__":
    print("--- Starting Data Preparation ---")

    # 1. Загрузка данных из Label Studio
    raw_data = load_label_studio_data(LABEL_STUDIO_EXPORT_FILE)

    if not raw_data:
        print("No data loaded. Exiting.")
        exit()

    # 2. Конвертация в формат spaCy
    spacy_formatted_data = convert_to_spacy_format(raw_data)

    if not spacy_formatted_data:
        print("No data after conversion. Exiting.")
        exit()

    # 3. Перемешивание данных перед разделением
    random.shuffle(spacy_formatted_data)

    # 4. Разделение на обучающий и валидационный наборы
    train_data, dev_data = train_test_split(
        spacy_formatted_data, test_size=DEV_SPLIT, random_state=42
    )  # random_state для воспроизводимости
    print(
        f"Data split complete: {len(train_data)} training examples, {len(dev_data)} development examples."
    )

    # 5. Создание папки для вывода (если не существует)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")

    # 6. Создание и сохранение DocBin для обучающего набора
    print("\n--- Creating Training Data (train.spacy) ---")
    create_docbin(train_data, TRAIN_DATA_FILE)

    # 7. Создание и сохранение DocBin для валидационного набора
    print("\n--- Creating Development Data (dev.spacy) ---")
    create_docbin(dev_data, DEV_DATA_FILE)

    print("\n--- Data Preparation Finished ---")
    print(f"Training data saved to: {TRAIN_DATA_FILE}")
    print(f"Development data saved to: {DEV_DATA_FILE}")
