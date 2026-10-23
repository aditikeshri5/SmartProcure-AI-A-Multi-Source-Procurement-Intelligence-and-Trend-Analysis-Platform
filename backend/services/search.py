import os, re, json, logging
from urllib.parse import urlparse
from datetime import datetime, timezone
from backend.nlp.extractor import parse_requirement
from backend.ml.source_ranker import rank_products
from backend.scraper.catalogue import scrape_product_page

log = logging.getLogger(__name__)
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

def discover_urls(query, limit=8):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return [], "Gemini API key is not configured. Add GEMINI_API_KEY to your .env file."
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        prompt = f"""Find up to {limit} relevant product or supplier pages for this procurement requirement: {query!r}.
Use web search. Prefer actual product listing/detail pages from credible retailers, manufacturers, or suppliers, not blogs, category homepages, or made-up URLs.
Return a JSON array only. Each object must contain url, reason. Do not invent URLs. Do not invent product prices."""
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.1
            )
        )
        text = response.text or ""
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            entries = json.loads(match.group(0))
            urls = []
            for item in entries:
                u = item.get("url","")
                if u.startswith(("http://","https://")) and urlparse(u).hostname:
                    urls.append({"url":u,"reason":item.get("reason","Relevant source")})
            return urls[:limit], None
        # Grounded responses may contain citations but not JSON; only accept literal URLs found in response.
        candidates = re.findall(r'https?://[^\s\]\[<>")]+', text)
        urls = []
        for u in candidates:
            u = u.rstrip(".,;")
            if urlparse(u).hostname and u not in [x["url"] for x in urls]:
                urls.append({"url":u,"reason":"Found in Gemini's web-grounded response"})
        return urls[:limit], None
    except Exception as exc:
        log.exception("Gemini discovery failed")
        return [], f"Gemini web discovery failed: {str(exc)[:220]}"

def _scrape_urls(urls, max_pages=6):
    products, errors, seen = [], [], set()
    for entry in urls[:max_pages]:
        url = entry["url"] if isinstance(entry,dict) else str(entry)
        try:
            item = scrape_product_page(url)
            key = re.sub(r'\W+','', (item.get("name") or "").lower())
            if key and key in seen: continue
            if key: seen.add(key)
            products.append(item)
        except Exception as exc:
            errors.append({"url":url,"error":str(exc)[:180]})
    return products, errors

def run_search(query):
    parsed = parse_requirement(query)
    urls, discovery_error = discover_urls(query)
    products, errors = _scrape_urls(urls)
    ranked = rank_products(products, query, parsed)[:3]
    return {
      "query": query, "parsed_requirement": parsed,
      "category": parsed.get("category_hint"),
      "products": ranked, "sources_found": len(urls),
      "sources_scraped": len(products), "source_errors": errors,
      "discovery_error": discovery_error,
      "generated_at": datetime.now(timezone.utc).isoformat(),
      "mode": "live_web_search"
    }

def extract_url(url, query=""):
    try:
        product = scrape_product_page(url)
        parsed = parse_requirement(query or product.get("name",""))
        product["category"] = __import__("backend.ml.source_ranker",fromlist=["classify_category"]).classify_category(
            product.get("name","") + " " + (product.get("description") or ""))
        ranked = rank_products([product], query or product.get("name",""), parsed)
        return {"query":query or url,"parsed_requirement":parsed,"products":ranked,
                "sources_found":1,"sources_scraped":1,"source_errors":[],
                "generated_at":datetime.now(timezone.utc).isoformat(),"mode":"direct_url"}
    except Exception as exc:
        return {"query":query or url,"parsed_requirement":parse_requirement(query),
                "products":[],"sources_found":1,"sources_scraped":0,
                "source_errors":[{"url":url,"error":str(exc)[:220]}],
                "generated_at":datetime.now(timezone.utc).isoformat(),"mode":"direct_url",
                "message":"We could not extract this page. It may block automated requests or load product details with JavaScript."}
