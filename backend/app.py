from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.services.search import search_products
from backend.database import init_db, get_stats
from backend.scraper.sources import scrape_page

app = Flask(__name__, static_folder="../frontend", static_url_path="/static")
init_db()

@app.get("/")
def index():
    return send_from_directory(ROOT / "frontend", "index.html")

@app.get("/api/stats")
def stats():
    return jsonify(get_stats())

@app.post("/api/search")
def search():
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query", "")).strip()
    if len(query) < 3:
        return jsonify({"error": "Please enter a requirement of at least 3 characters."}), 400
    try:
        budget = float(payload["budget"]) if payload.get("budget") not in (None, "") else None
        quantity = max(1, int(payload.get("quantity", 1)))
        if budget is not None and budget <= 0:
            budget = None
    except (ValueError, TypeError):
        return jsonify({"error": "Budget must be a positive number and quantity must be a whole number."}), 400
    result = search_products(query, budget=budget, quantity=quantity)
    return jsonify(result)

@app.post("/api/scrape")
def scrape():
    payload = request.get_json(silent=True) or {}
    url = str(payload.get("url", "")).strip()
    result, status = scrape_page(url)
    return jsonify(result), status

if __name__ == "__main__":
    app.run(debug=True, port=5000)
