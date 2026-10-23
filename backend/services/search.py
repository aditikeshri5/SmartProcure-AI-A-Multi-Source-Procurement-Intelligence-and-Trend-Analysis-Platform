import re
from backend.database import get_products
from backend.ml.source_ranker import predict_category, model_info
from backend.nlp.extractor import extract_requirements

def search_products(query, budget=None, quantity=1):
    extracted = extract_requirements(query)
    if budget is None:
        budget = extracted["budget_detected"]
    quantity = max(1, int(quantity or extracted["quantity_detected"] or 1))
    category = predict_category(query)
    query_words = set(re.findall(r"[a-z0-9]+", query.lower()))
    products = get_products()
    ranked = []
    for p in products:
        searchable = f'{p["name"]} {p["category"]} {p.get("specs") or ""}'.lower()
        overlap = sum(1 for word in query_words if len(word) > 2 and word in searchable)
        category_match = p["category"] == category
        within_budget = budget is None or p["price"] <= budget
        budget_score = 2.0 if within_budget and budget is not None else (0.0 if budget is None else -2.0)
        score = (4 if category_match else 0) + overlap + budget_score + float(p.get("rating") or 0) / 5
        p.update({
            "score": round(score, 2),
            "within_budget": within_budget,
            "estimated_total": round(float(p["price"]) * quantity, 2)
        })
        ranked.append(p)
    # First prefer category matches. Within them, prioritize budget fit and relevance score.
    matches = [p for p in ranked if p["category"] == category]
    pool = matches if matches else ranked
    pool.sort(key=lambda p: (p["within_budget"], p["score"], p["rating"]), reverse=True)
    return {
        "query": query,
        "predicted_category": category,
        "extracted_requirements": extracted,
        "budget_used": budget,
        "quantity_used": quantity,
        "total_products_checked": len(products),
        "recommendations": pool[:3],
        "model": model_info(),
        "notice": "Demo catalogue: prices, ratings and supplier names are illustrative and are not live quotations."
    }
