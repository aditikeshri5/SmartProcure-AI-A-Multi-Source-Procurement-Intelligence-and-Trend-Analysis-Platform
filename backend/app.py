import os
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, jsonify, request, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database.db import init_db, get_db
from backend.services.search import run_search, extract_url
from backend.database.db import create_search, get_searches, get_search, delete_search, clear_searches

app = Flask(__name__, template_folder="../frontend", static_folder="../frontend", static_url_path="/static")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-before-deployment")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("COOKIE_SECURE", "0") == "1"
init_db()

def api_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status

def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return api_error("Please log in to continue.", 401)
        return fn(*args, **kwargs)
    return wrapped

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/login")
def login_page():
    return render_template("index.html")

@app.get("/register")
def register_page():
    return render_template("index.html")

@app.get("/dashboard")
def dashboard_page():
    return render_template("index.html")

@app.get("/api/me")
def me():
    if not session.get("user_id"):
        return jsonify({"authenticated": False})
    return jsonify({"authenticated": True, "user": {
        "id": session["user_id"], "name": session["name"],
        "email": session["email"], "account_type": session["account_type"]
    }})

@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    account_type = data.get("account_type", "individual")
    company = (data.get("company_name") or "").strip()
    website = (data.get("website") or "").strip()
    if not name or not email or not password:
        return api_error("Name, email and password are required.")
    if "@" not in email or "." not in email.split("@")[-1]:
        return api_error("Enter a valid email address.")
    if len(password) < 8:
        return api_error("Password must be at least 8 characters.")
    if account_type not in ("individual", "organization"):
        return api_error("Choose an individual or organization account.")
    if account_type == "organization" and not company:
        return api_error("Company/organization name is required.")
    db = get_db()
    try:
        cur = db.execute("""INSERT INTO users(name,email,password_hash,account_type,company_name,website,created_at)
            VALUES(?,?,?,?,?,?,?)""",
            (name, email, generate_password_hash(password), account_type, company, website, datetime.now(timezone.utc).isoformat()))
        db.commit()
        user_id = cur.lastrowid
    except Exception as exc:
        db.close()
        if "UNIQUE" in str(exc).upper():
            return api_error("An account with this email already exists.", 409)
        app.logger.exception("Registration failed")
        return api_error("Unable to create account right now.", 500)
    db.close()
    session.clear()
    session.update(user_id=user_id, name=name, email=email, account_type=account_type)
    return jsonify({"ok": True, "user": {"id": user_id, "name": name, "email": email, "account_type": account_type}}), 201

@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email, password = (data.get("email") or "").strip().lower(), data.get("password") or ""
    if not email or not password:
        return api_error("Email and password are required.")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    db.close()
    if not user or not check_password_hash(user["password_hash"], password):
        return api_error("Email or password is incorrect.", 401)
    session.clear()
    session.update(user_id=user["id"], name=user["name"], email=user["email"], account_type=user["account_type"])
    return jsonify({"ok": True, "user": {"id": user["id"], "name": user["name"], "email": user["email"], "account_type": user["account_type"]}})

@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.post("/api/search")
def search():
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    url = (data.get("url") or "").strip()
    if not query and not url:
        return api_error("Enter a procurement requirement or a product page URL.")
    if url:
        result = extract_url(url, query=query)
        mode = "url"
    else:
        result = run_search(query)
        mode = "search"
    if not result.get("products"):
        result.setdefault("message", "No extractable product details were found. Try a more specific requirement or a direct product URL.")
    history_id = None
    if session.get("user_id"):
        history_id = create_search(session["user_id"], query or url, mode, result)
    result["history_id"] = history_id
    result["searched_at"] = datetime.now(timezone.utc).isoformat()
    return jsonify({"ok": True, **result})

@app.get("/api/history")
@login_required
def history():
    return jsonify({"ok": True, "items": get_searches(session["user_id"])})

@app.get("/api/history/<int:search_id>")
@login_required
def history_detail(search_id):
    item = get_search(session["user_id"], search_id)
    if not item:
        return api_error("Saved search not found.", 404)
    return jsonify({"ok": True, "item": item})

@app.delete("/api/history/<int:search_id>")
@login_required
def history_delete(search_id):
    if not delete_search(session["user_id"], search_id):
        return api_error("Saved search not found.", 404)
    return jsonify({"ok": True})

@app.delete("/api/history")
@login_required
def history_clear():
    clear_searches(session["user_id"])
    return jsonify({"ok": True})

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "SmartProcure AI"})

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
