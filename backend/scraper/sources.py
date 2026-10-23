"""Basic public-page metadata and text scraper for demonstration purposes."""
from urllib.parse import urlparse
import re
import requests
from bs4 import BeautifulSoup

def scrape_page(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return {"error": "Enter a valid public http:// or https:// URL."}, 400
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
        return {"error": "Local URLs are not supported."}, 400
    try:
        response = requests.get(url, timeout=8, headers={"User-Agent": "SmartProcureAI-StudentDemo/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled page"
        meta = soup.find("meta", attrs={"name": "description"})
        description = meta.get("content", "") if meta else ""
        text = " ".join(soup.stripped_strings)
        price_mentions = re.findall(r"(?:₹|Rs\.?|INR|\$)\s?[\d,]+(?:\.\d{1,2})?", text, flags=re.I)
        return {
            "title": title[:200], "description": description[:500],
            "text_preview": text[:1000], "price_mentions": price_mentions[:10],
            "source_url": url,
            "warning": "Basic page extraction only. Respect site terms and robots policy; some pages block requests or require JavaScript."
        }, 200
    except requests.RequestException as exc:
        return {"error": f"Could not fetch page: {str(exc)[:180]}"}, 502
