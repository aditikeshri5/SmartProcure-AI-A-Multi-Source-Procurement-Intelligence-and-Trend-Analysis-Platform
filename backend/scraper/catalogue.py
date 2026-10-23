import json, re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from backend.scraper.sources import validate_public_url

HEADERS = {"User-Agent": "SmartProcureAI/1.0 (+product research; respectful, low-volume fetching)"}

def scrape_product_page(url):
    validate_public_url(url)
    response = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
    response.raise_for_status()
    if len(response.content) > 5_000_000:
        raise ValueError("Page is too large to process safely.")
    content_type = response.headers.get("content-type","")
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        raise ValueError("The URL did not return an HTML page.")
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script","style","noscript","svg","iframe"]): tag.decompose()
    canonical = soup.find("link", rel=lambda v: v and "canonical" in v)
    title_tag = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name":"twitter:title"})
    name = (title_tag.get("content") if title_tag else None) or (soup.title.get_text(" ", strip=True) if soup.title else None)
    description_tag = soup.find("meta", attrs={"name":"description"}) or soup.find("meta", property="og:description")
    description = description_tag.get("content","") if description_tag else ""
    price = None
    currency = None
    availability = None
    supplier = urlparse(response.url).netloc.removeprefix("www.")
    product_json = None
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or script.get_text())
            stack = data if isinstance(data,list) else [data]
            while stack:
                node = stack.pop()
                if isinstance(node,dict):
                    if node.get("@type") == "Product" or (isinstance(node.get("@type"),list) and "Product" in node["@type"]):
                        product_json = node; break
                    if isinstance(node.get("@graph"),list): stack.extend(node["@graph"])
                elif isinstance(node,list): stack.extend(node)
            if product_json: break
        except Exception:
            continue
    if product_json:
        name = product_json.get("name") or name
        description = product_json.get("description") or description
        brand = product_json.get("brand")
        if isinstance(brand,dict): supplier = brand.get("name") or supplier
        offers = product_json.get("offers")
        if isinstance(offers,list): offers = offers[0] if offers else {}
        if isinstance(offers,dict):
            try: price = float(str(offers.get("price") or offers.get("lowPrice")).replace(",",""))
            except (ValueError, TypeError): pass
            currency = offers.get("priceCurrency")
            availability = (offers.get("availability") or "").split("/")[-1] or None
    if price is None:
        for selector in [
            ('meta', {'property':'product:price:amount'}),
            ('meta', {'itemprop':'price'}),
            ('meta', {'name':'twitter:data1'})
        ]:
            tag = soup.find(selector[0], attrs=selector[1])
            if tag:
                raw = tag.get("content") or tag.get("value") or tag.get_text(" ",strip=True)
                m = re.search(r'[\d,]+(?:\.\d{1,2})?', raw or "")
                if m:
                    try: price=float(m.group(0).replace(",","")); break
                    except ValueError: pass
    if not name: name = "Product details"
    specs = []
    for row in soup.select("tr"):
        cells = [c.get_text(" ",strip=True) for c in row.select("th,td")]
        if len(cells) >= 2 and all(cells[:2]): specs.append(f"{cells[0]}: {cells[1]}")
    text = soup.get_text(" ", strip=True)
    if not description: description = text[:500]
    return {
      "name": name[:250], "description": description[:1200], "price": price,
      "currency": currency or ("INR" if "₹" in text else None), "availability": availability,
      "supplier": supplier, "specifications": "; ".join(specs[:12]) or None,
      "source_url": response.url, "source_domain": supplier,
      "extracted_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
      "status": "extracted", "canonical_url": canonical.get("href") if canonical else None
    }
