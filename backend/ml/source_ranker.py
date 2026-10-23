"""Small, real TF-IDF + Logistic Regression category classifier."""
from pathlib import Path
import csv

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "training_data.csv"

FALLBACK_ROWS = [
    ("laptop computer notebook smartphone mobile phone monitor printer", "electronics"),
    ("gaming laptop phone tablet electronic device", "electronics"),
    ("office chair desk table cabinet sofa shelf furniture", "furniture"),
    ("ergonomic chair wooden desk storage cabinet", "furniture"),
    ("paper notebook pen stapler folders stationery office supplies", "office"),
    ("copy paper markers files pens office stationery", "office"),
    ("safety helmet gloves protective boots goggles mask", "safety"),
    ("industrial safety equipment reflective vest", "safety"),
    ("network switch router ethernet cable wifi access point", "networking"),
    ("internet router firewall network switch", "networking"),
]

def load_training_rows():
    rows = []
    if DATA_PATH.exists():
        with DATA_PATH.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                text = (row.get("text") or row.get("requirement") or row.get("product") or "").strip()
                label = (row.get("category") or row.get("label") or "").strip().lower()
                if text and label:
                    rows.append((text, label))
    return rows if len(rows) >= 4 and len({label for _, label in rows}) >= 2 else FALLBACK_ROWS

TRAINING_ROWS = load_training_rows()
model = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2), stop_words="english")),
    ("classifier", LogisticRegression(max_iter=1000, random_state=42))
])
model.fit([text for text, _ in TRAINING_ROWS], [label for _, label in TRAINING_ROWS])

def predict_category(text):
    return str(model.predict([text])[0])

def model_info():
    return {"model": "TF-IDF + Logistic Regression", "training_examples": len(TRAINING_ROWS), "categories": sorted(set(label for _, label in TRAINING_ROWS))}
