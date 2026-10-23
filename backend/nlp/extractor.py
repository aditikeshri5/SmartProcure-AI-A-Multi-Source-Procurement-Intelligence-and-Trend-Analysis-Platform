import re

def extract_requirements(text):
    """Lightweight rule-based extraction; ML category prediction happens separately."""
    text = str(text or "").strip()
    budget = None
    quantity = 1
    budget_match = re.search(r"(?:under|below|budget(?:\s+of)?|less than|within)\s*(?:₹|rs\.?|inr)?\s*([\d,]+)", text, re.I)
    if not budget_match:
        budget_match = re.search(r"(?:₹|rs\.?|inr)\s*([\d,]+)", text, re.I)
    if budget_match:
        try:
            budget = float(budget_match.group(1).replace(",", ""))
        except ValueError:
            pass
    qty_match = re.search(r"\b(\d+)\s*(?:units?|items?|pieces?|laptops?|chairs?|computers?|printers?|routers?)\b", text, re.I)
    if qty_match:
        quantity = max(1, int(qty_match.group(1)))
    cleaned = re.sub(r"\s+", " ", text)
    return {"original_text": text, "budget_detected": budget, "quantity_detected": quantity, "normalized_requirement": cleaned}
