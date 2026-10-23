import re

def parse_requirement(text):
    text = (text or "").strip()
    budget = None
    match = re.search(r'(?:under|below|less than|within|budget(?: of)?|upto|up to)\s*(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)', text, re.I)
    if not match:
        match = re.search(r'(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)', text, re.I)
    if match:
        try: budget = float(match.group(1).replace(",", ""))
        except ValueError: pass
    qty = None
    qm = re.search(r'\b(?:quantity|qty|need|buy|purchase|order)\s*(?:of|:)?\s*(\d+)\b|\b(\d+)\s*(?:units|pieces|pcs|items)\b', text, re.I)
    if qm:
        qty = int(next(g for g in qm.groups() if g))
    lower = text.lower()
    category = "general"
    categories = {
      "laptop": ["laptop","notebook","ultrabook"],
      "monitor": ["monitor","display","screen"],
      "office furniture": ["chair","desk","table","cabinet","furniture"],
      "networking": ["router","switch","access point","network"],
      "printer": ["printer","scanner","multifunction"],
      "mobile": ["smartphone","mobile phone","phone","tablet"],
      "storage": ["ssd","hard drive","hdd","storage drive"],
      "projector": ["projector"],
      "safety equipment": ["safety helmet","safety shoes","ppe","safety equipment"],
    }
    for cat, terms in categories.items():
        if any(term in lower for term in terms):
            category = cat
            break
    specs = []
    for pattern in [r'\b\d+\s?gb\s?(?:ram|memory)?\b', r'\b\d+\s?tb\b', r'\b\d+(?:\.\d+)?\s?(?:inch|inches|")\b',
                    r'\b(?:i[3579]-?\d{4,5}|ryzen\s?[3579]\s?\d{3,4}|4k|1080p|wifi\s?6)\b']:
        specs.extend(m.group(0) for m in re.finditer(pattern, lower, re.I))
    return {"raw": text, "budget": budget, "quantity": qty, "category_hint": category, "specifications": sorted(set(specs))}
