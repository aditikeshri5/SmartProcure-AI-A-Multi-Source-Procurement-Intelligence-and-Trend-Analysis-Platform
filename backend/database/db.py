import json, os, sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(os.getenv("SMARTPROCURE_DB", Path(__file__).resolve().parents[2] / "data" / "smartprocure.db"))

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL, account_type TEXT NOT NULL DEFAULT 'individual',
      company_name TEXT, website TEXT, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS searches(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
      input_text TEXT NOT NULL, mode TEXT NOT NULL, result_json TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'completed', created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_searches_user_created ON searches(user_id, created_at DESC);
    """)
    db.commit()
    db.close()

def create_search(user_id, input_text, mode, result):
    db = get_db()
    cur = db.execute("INSERT INTO searches(user_id,input_text,mode,result_json,status,created_at) VALUES(?,?,?,?,?,?)",
        (user_id, input_text, mode, json.dumps(result, ensure_ascii=False), "completed",
         datetime.now(timezone.utc).isoformat()))
    db.commit()
    search_id = cur.lastrowid
    db.close()
    return search_id

def get_searches(user_id):
    db = get_db()
    rows = db.execute("SELECT id,input_text,mode,status,created_at FROM searches WHERE user_id=? ORDER BY id DESC LIMIT 100", (user_id,)).fetchall()
    db.close()
    return [dict(r) for r in rows]

def get_search(user_id, search_id):
    db = get_db()
    row = db.execute("SELECT * FROM searches WHERE id=? AND user_id=?", (search_id,user_id)).fetchone()
    db.close()
    if not row: return None
    item = dict(row)
    item["result"] = json.loads(item.pop("result_json"))
    return item

def delete_search(user_id, search_id):
    db = get_db()
    cur = db.execute("DELETE FROM searches WHERE id=? AND user_id=?", (search_id,user_id))
    db.commit(); db.close()
    return cur.rowcount > 0

def clear_searches(user_id):
    db = get_db()
    db.execute("DELETE FROM searches WHERE user_id=?", (user_id,))
    db.commit(); db.close()
