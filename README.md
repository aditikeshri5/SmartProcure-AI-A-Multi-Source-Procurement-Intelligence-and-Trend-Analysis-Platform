# SmartProcure AI

## Run on Windows
Open a terminal in the project root folder (the folder containing `backend`, `frontend`, `data`, and `requirements.txt`).

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe backend\app.py
```

Open http://127.0.0.1:5000

If installation is successful, the app will create `data/smartprocure.db` automatically.

## What is implemented
- Flask API and frontend dashboard
- SQLite demo product catalogue
- CSV-driven TF-IDF + Logistic Regression category classifier
- Basic requirement extraction for budget and quantity
- Top-three category/product recommendations with a transparent heuristic score
- Basic public page scraper for title, description, text preview, and price mentions

## Honest limitations
- The product catalogue uses illustrative sample data, not live market offers.
- The scraper does not support every site and does not automatically add scraped results to the database.
- The ML training dataset is intentionally small for a working demo; it is not evidence of production-level accuracy.
- The ranking score is a heuristic, not a separately trained ranking model.
- Before deployment, add tests, stronger URL/IP protections, authentication, logging, and site-specific scraping compliance.
