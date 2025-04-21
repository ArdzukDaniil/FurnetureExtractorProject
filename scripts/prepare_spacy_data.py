import json
import spacy
from spacy.tokens import DocBin, Span
import random
import os
from sklearn.model_selection import train_test_split


LABEL_STUDIO_EXPORT_FILE = os.path.join(
    "../data", "annotated", "spacy_training_data.json"
)


OUTPUT_DIR = os.path.join("../data", "spacy_data")


TRAIN_DATA_FILE = os.path.join(OUTPUT_DIR, "train.spacy")
DEV_DATA_FILE = os.path.join(OUTPUT_DIR, "dev.spacy")


DEV_SPLIT = 0.2


TARGET_LABEL = "PRODUCT"


NLP_MODEL = "en_core_web_sm"

try:
    nlp = spacy.load(NLP_MODEL)
    print(f"Loaded spaCy model '{NLP_MODEL}' for tokenization.")
except OSError:
    print(f"spaCy model '{NLP_MODEL}' not found. Trying blank 'en' model.")
    nlp = spacy.blank("en")
    print(
        "Using blank 'en' model. Consider downloading a pretrained model for better tokenization: python -m spacy download en_core_web_sm"
    )





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
        )

        if not text or not isinstance(text, str):
            print(f"Warning: Skipping record due to missing or invalid text: {record}")
            skipped_count += 1
            continue

        formatted_entities = []
        if isinstance(entities, list):
            for ent in entities:

                if isinstance(ent, list) and len(ent) == 3:
                    start, end, label = ent

                    if (
                        isinstance(start, int)
                        and isinstance(end, int)
                        and isinstance(label, str)
                    ):
                        if label == TARGET_LABEL:

                            if 0 <= start < len(text) and start < end <= len(text):
                                formatted_entities.append((start, end, label))
                            else:
                                print(
                                    f"Warning: Skipping invalid entity indices {ent} for text snippet: '{text[:50]}...'"
                                )

                    else:
                        print(f"Warning: Skipping entity with invalid types: {ent}")
                else:
                    print(f"Warning: Skipping malformed entity entry: {ent}")
        elif entities is not None:
            print(f"Warning: 'entities' field is not a list in record: {record}")


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
        doc = nlp.make_doc(text)
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


        try:
            doc.ents = ents
        except ValueError as e:

            print(
                f"Warning: Could not set entities for doc (possibly overlapping spans?): {e}"
            )

            print(f"Text snippet: {text[:100]}...")
            print(
                f"Problematic ents: {[(e.start_char, e.end_char, e.label_) for e in ents]}"
            )

        db.add(doc)

    db.to_disk(output_file)
    print(f"Saved {len(data)} documents to {output_file}")
    if skipped_spans > 0:
        print(
            f"Skipped {skipped_spans}/{total_spans} entity spans due to alignment issues."
        )
    if skipped_spans == total_spans and total_spans > 0:
        print(
            "ERROR: All entity spans were skipped. Check your annotation indices and text processing."
        )


if __name__ == "__main__":
    print("--- Starting Data Preparation ---")


    raw_data = load_label_studio_data(LABEL_STUDIO_EXPORT_FILE)

    if not raw_data:
        print("No data loaded. Exiting.")
        exit()


    spacy_formatted_data = convert_to_spacy_format(raw_data)

    if not spacy_formatted_data:
        print("No data after conversion. Exiting.")
        exit()


    random.shuffle(spacy_formatted_data)


    train_data, dev_data = train_test_split(
        spacy_formatted_data, test_size=DEV_SPLIT, random_state=42
    )
    print(
        f"Data split complete: {len(train_data)} training examples, {len(dev_data)} development examples."
    )


    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")


    print("\n--- Creating Training Data (train.spacy) ---")
    create_docbin(train_data, TRAIN_DATA_FILE)


    print("\n--- Creating Development Data (dev.spacy) ---")
    create_docbin(dev_data, DEV_DATA_FILE)

    print("\n--- Data Preparation Finished ---")
    print(f"Training data saved to: {TRAIN_DATA_FILE}")
    print(f"Development data saved to: {DEV_DATA_FILE}")
