
import re
import logging
from urllib.parse import urlparse
from datetime import datetime, timezone

from backend.nlp.extractor import parse_requirement
from backend.ml.source_ranker import rank_products
from backend.scraper.catalogue import scrape_product_page

log = logging.getLogger(__name__)


def discover_urls(query, limit=8):
    """Discover product and supplier pages using web text search."""
    try:
        from ddgs import DDGS

        # Search for actual product pages, not just general information.
        search_queries = [
            f"{query} buy price product",
            f"{query} official store supplier",
        ]

        urls = []
        seen = set()

        with DDGS() as ddgs:
            for search_query in search_queries:
                results = ddgs.text(
                    search_query,
                    region="in-en",
                    max_results=limit
                )

                for result in results or []:
                    url = result.get("href") or result.get("url") or ""

                    if not url.startswith(("http://", "https://")):
                        continue

                    parsed_url = urlparse(url)
                    hostname = (parsed_url.hostname or "").lower()

                    if not hostname or hostname in seen:
                        continue

                    # Skip obvious non-product and search pages.
                    if any(
                        domain in hostname
                        for domain in (
                            "duckduckgo.com",
                            "google.com",
                            "bing.com",
                            "youtube.com",
                            "facebook.com",
                            "instagram.com",
                        )
                    ):
                        continue

                    seen.add(hostname)
                    urls.append({
                        "url": url,
                        "reason": result.get(
                            "title", "Found through web search"
                        )
                    })

                    if len(urls) >= limit:
                        break

                if len(urls) >= limit:
                    break

        if not urls:
            return [], "Web search returned no usable product URLs."

        return urls[:limit], None

    except Exception as exc:
        log.exception("Web discovery failed")
        return [], f"Web discovery failed: {str(exc)[:220]}"


def _scrape_urls(urls, max_pages=6):
    products, errors, seen = [], [], set()

    for entry in urls[:max_pages]:
        url = entry["url"] if isinstance(entry, dict) else str(entry)

        try:
            item = scrape_product_page(url)
            key = re.sub(
                r"\W+", "", (item.get("name") or "").lower()
            )

            if key and key in seen:
                continue

            if key:
                seen.add(key)

            products.append(item)

        except Exception as exc:
            errors.append({
                "url": url,
                "error": str(exc)[:180]
            })

    return products, errors


def run_search(query):
    parsed = parse_requirement(query)
    urls, discovery_error = discover_urls(query)
    products, errors = _scrape_urls(urls)
    ranked = rank_products(products, query, parsed)[:3]

    return {
        "query": query,
        "parsed_requirement": parsed,
        "category": parsed.get("category_hint"),
        "products": ranked,
        "sources_found": len(urls),
        "sources_scraped": len(products),
        "source_errors": errors,
        "discovery_error": discovery_error,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live_web_search"
    }


def extract_url(url, query=""):
    try:
        product = scrape_product_page(url)
        parsed = parse_requirement(query or product.get("name", ""))

        product["category"] = (
            __import__(
                "backend.ml.source_ranker",
                fromlist=["classify_category"]
            ).classify_category(
                product.get("name", "")
                + " "
                + (product.get("description") or "")
            )
        )

        ranked = rank_products(
            [product],
            query or product.get("name", ""),
            parsed
        )

        return {
            "query": query or url,
            "parsed_requirement": parsed,
            "products": ranked,
            "sources_found": 1,
            "sources_scraped": 1,
            "source_errors": [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "direct_url"
        }

    except Exception as exc:
        return {
            "query": query or url,
            "parsed_requirement": parse_requirement(query),
            "products": [],
            "sources_found": 1,
            "sources_scraped": 0,
            "source_errors": [{
                "url": url,
                "error": str(exc)[:220]
            }],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "direct_url",
            "message": (
                "We could not extract this page. It may block "
                "automated requests or load product details with JavaScript."
            )
        }
