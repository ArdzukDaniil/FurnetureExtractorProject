import spacy
from spacy.tokens import DocBin
from spacy.scorer import Scorer, Example
import os

# --- Конфигурация ---
MODEL_PATH = os.path.join("../training", "model-best")
DEV_DATA_PATH = os.path.join("../data", "spacy_data", "dev.spacy")
MAX_EXAMPLES_TO_SHOW = 10

# --- Загрузка ---
print(f"Loading model from: {MODEL_PATH}")
try:
    nlp = spacy.load(MODEL_PATH)
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

print(f"Loading development data from: {DEV_DATA_PATH}")
try:
    db = DocBin().from_disk(DEV_DATA_PATH)
    dev_docs = list(db.get_docs(nlp.vocab))
except Exception as e:
    print(f"Error loading development data: {e}")
    exit()

print(f"Loaded {len(dev_docs)} documents for analysis.")

false_positives = []
false_negatives = []
boundary_errors = []

examples = []
for gold_doc in dev_docs:
    if not gold_doc.text.strip():
        continue

    pred_doc = nlp(gold_doc.text)
    examples.append(Example(pred_doc, gold_doc))

    gold_spans = set(
        [(ent.start_char, ent.end_char, ent.label_) for ent in gold_doc.ents]
    )
    pred_spans = set(
        [(ent.start_char, ent.end_char, ent.label_) for ent in pred_doc.ents]
    )

    for start, end, label in pred_spans:
        if (start, end, label) not in gold_spans:

            is_boundary = False
            for g_start, g_end, g_label in gold_spans:
                if label == g_label and max(start, g_start) < min(end, g_end):
                    is_boundary = True
                    break
            if not is_boundary:
                false_positives.append(
                    {
                        "text": pred_doc.text[
                                max(0, start - 30): min(len(pred_doc.text), end + 30)
                                ],
                        "prediction": pred_doc.text[start:end],
                        "indices": (start, end),
                    }
                )

    for start, end, label in gold_spans:
        if (start, end, label) not in pred_spans:

            is_boundary = False
            for p_start, p_end, p_label in pred_spans:
                if label == p_label and max(start, p_start) < min(end, p_end):
                    is_boundary = True

                    pred_span_text = pred_doc.text[p_start:p_end]
                    boundary_errors.append(
                        {
                            "text": gold_doc.text[
                                    max(0, start - 30): min(len(gold_doc.text), end + 30)
                                    ],
                            "gold_standard": gold_doc.text[start:end],
                            "gold_indices": (start, end),
                            "prediction": pred_span_text,
                            "pred_indices": (p_start, p_end),
                        }
                    )
                    break
            if not is_boundary:
                false_negatives.append(
                    {
                        "text": gold_doc.text[
                                max(0, start - 30): min(len(gold_doc.text), end + 30)
                                ],
                        "missed_entity": gold_doc.text[start:end],
                        "indices": (start, end),
                    }
                )

print("\n--- Error Analysis ---")

print(f"\n--- False Positives (Predicted as PRODUCT, but shouldn't be) ---")
if false_positives:
    for i, fp in enumerate(false_positives[:MAX_EXAMPLES_TO_SHOW]):
        print(f"{i + 1}. Prediction: '{fp['prediction']}' ({fp['indices']})")
        print(f"   Context: ...{fp['text']}...")
else:
    print("No false positives found.")

print(f"\n--- False Negatives (Should be PRODUCT, but was missed) ---")
if false_negatives:
    for i, fn in enumerate(false_negatives[:MAX_EXAMPLES_TO_SHOW]):
        print(f"{i + 1}. Missed: '{fn['missed_entity']}' ({fn['indices']})")
        print(f"   Context: ...{fn['text']}...")
else:
    print("No false negatives found.")

print(f"\n--- Boundary Errors (Overlap exists, but boundaries differ) ---")
if boundary_errors:
    for i, be in enumerate(boundary_errors[:MAX_EXAMPLES_TO_SHOW]):
        print(f"{i + 1}. Gold: '{be['gold_standard']}' ({be['gold_indices']})")
        print(f"   Pred: '{be['prediction']}' ({be['pred_indices']})")
        print(f"   Context: ...{be['text']}...")
else:
    print("No boundary errors found.")

print("\n--- Overall Scorer Metrics (Confirmation) ---")
scorer = Scorer()
scores = scorer.score(examples)
print(scores["ents_per_type"])
