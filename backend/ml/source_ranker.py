from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

TRAINING = [
("laptop","business laptop notebook computer portable workstation"),
("laptop","16 gb ram laptop ssd intel ryzen notebook"),
("monitor","computer monitor display screen 24 inch 4k"),
("office furniture","office chair ergonomic desk table cabinet"),
("networking","wifi router ethernet network switch access point"),
("printer","laser printer inkjet scanner multifunction"),
("mobile","smartphone mobile phone android tablet"),
("storage","ssd hard drive external storage hdd"),
("projector","office projector presentation display"),
("safety equipment","industrial safety helmet gloves protective shoes"),
("audio","headphones microphone speaker conference audio"),
("appliance","air conditioner refrigerator appliance"),
("general","procurement product supply equipment item")
]
_model = None
def _get_model():
    global _model
    if _model is None:
        x, y = zip(*TRAINING)
        _model = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)),
                           ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
        _model.fit(x, y)
    return _model

def classify_category(text):
    try:
        model = _get_model()
        return str(model.predict([text])[0])
    except Exception:
        return "general"

def rank_products(products, requirement, parsed=None):
    parsed = parsed or {}
    words = {w.lower() for w in requirement.split() if len(w) > 2}
    budget = parsed.get("budget")
    for product in products:
        title = (product.get("name") or "").lower()
        details = " ".join(str(product.get(k) or "") for k in ("description","specifications","supplier")).lower()
        combined = title + " " + details
        overlap = len(words & set(combined.split())) / max(1, len(words))
        score = overlap * 65
        price = product.get("price")
        if isinstance(price, (int,float)) and budget:
            score += 25 if price <= budget else max(0, 25 - ((price-budget)/max(budget,1))*50)
        elif price is not None:
            score += 5
        if product.get("name"): score += 5
        if product.get("source_url"): score += 5
        product["relevance_score"] = round(min(100, score), 1)
        product["category"] = classify_category((product.get("name") or "") + " " + (product.get("description") or ""))
        product["budget_match"] = (price <= budget) if isinstance(price,(int,float)) and budget else None
    return sorted(products, key=lambda p: p.get("relevance_score",0), reverse=True)
