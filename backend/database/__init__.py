"""SQLite database setup and data access."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "smartprocure.db"

SEED_PRODUCTS = [
    ("OfficePro Laptop 14", "electronics", 48900, "16GB RAM, 512GB SSD, 14-inch", 4.4, "Demo supplier A"),
    ("WorkMate Laptop 15", "electronics", 55900, "16GB RAM, 1TB SSD, 15.6-inch", 4.6, "Demo supplier B"),
    ("ValueBook Laptop", "electronics", 38900, "8GB RAM, 512GB SSD, 15.6-inch", 4.1, "Demo supplier C"),
    ("ProView Monitor 27", "electronics", 18900, "27-inch, IPS, Full HD", 4.5, "Demo supplier A"),
    ("Ergo Office Chair", "furniture", 8500, "Adjustable height, lumbar support", 4.6, "Demo supplier D"),
    ("Executive Office Desk", "furniture", 12400, "Engineered wood, cable management", 4.2, "Demo supplier B"),
    ("Compact Storage Cabinet", "furniture", 6900, "3 shelves, lockable doors", 4.0, "Demo supplier C"),
    ("A4 Copy Paper Box", "office", 1450, "5 reams, 500 sheets per ream", 4.3, "Demo supplier E"),
    ("Stationery Starter Kit", "office", 850, "Pens, notebooks, markers, folders", 4.1, "Demo supplier A"),
    ("Industrial Safety Helmet", "safety", 650, "Adjustable, impact-resistant shell", 4.4, "Demo supplier F"),
    ("Protective Safety Goggles", "safety", 320, "Anti-scratch clear lens", 4.2, "Demo supplier F"),
    ("Gigabit Network Switch", "networking", 3200, "8-port gigabit ethernet", 4.5, "Demo supplier B"),
    ("Dual-Band Wi-Fi Router", "networking", 2800, "Dual-band, 4 antennas", 4.3, "Demo supplier C"),
    ("Industrial Work Gloves", "safety", 450, "Cut-resistant coated gloves", 4.1, "Demo supplier F"),
    ("Office Printer", "electronics", 12900, "Wireless laser printer, duplex printing", 4.2, "Demo supplier E"),
]

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, category TEXT NOT NULL, price REAL NOT NULL,
            specs TEXT, rating REAL DEFAULT 0, supplier TEXT,
            source TEXT DEFAULT 'Demo dataset'
        )""")
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO products (name,category,price,specs,rating,supplier,source) VALUES (?,?,?,?,?,?,?)",
                [(*p, "Demo dataset") for p in SEED_PRODUCTS]
            )

def get_products():
    with _connect() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM products").fetchall()]

def get_stats():
    products = get_products()
    return {"product_count": len(products), "categories": len({p["category"] for p in products}), "database": "SQLite"}
