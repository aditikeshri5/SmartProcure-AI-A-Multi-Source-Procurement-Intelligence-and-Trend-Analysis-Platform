"""Product catalogue helper. Live scraped pages are not automatically trusted as product records."""
from backend.database import get_products

def get_catalogue():
    return get_products()
