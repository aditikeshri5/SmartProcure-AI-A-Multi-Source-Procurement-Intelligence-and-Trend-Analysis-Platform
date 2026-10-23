# SmartProcure AI

A Flask-based procurement research MVP that discovers product pages using Gemini web search grounding, scrapes accessible pages, ranks extracted results, and stores account-specific search history in SQLite.

## Important behaviour

- **No static product catalogue is used for search results.** Results come from Gemini web-grounded URL discovery followed by webpage extraction, or from a user-provided product URL.
- Product details are source-dependent. Websites may block automated access or render details with JavaScript. Missing values are displayed as unavailable rather than guessed.
- The app only fetches publicly accessible HTTP/HTTPS URLs, uses request timeouts and a response-size limit, and does not attempt to bypass access controls. Review each site's terms and robots policies before deploying or increasing scraping volume.
- Category classification uses a small built-in text training set for the MVP. For a graded ML project, replace/expand it with a labelled dataset and evaluate model quality before claiming production accuracy.
- Login history is stored in SQLite; passwords are hashed using Werkzeug. Set a strong `SECRET_KEY` and use HTTPS / `COOKIE_SECURE=1` before deployment.

## Run locally (Windows PowerShell)

1. Open this folder in VS Code.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env`, then add your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). Keep the key in `.env`, never in frontend JavaScript.

   ```powershell
   Copy-Item .env.example .env
   ```

5. Start the app:

   ```powershell
   python -m backend.app
   ```

6. Open `http://127.0.0.1:5000`.

## Folder structure

```text
SmartProcure_AI/
├── backend/
│   ├── app.py
│   ├── database/db.py
│   ├── ml/source_ranker.py
│   ├── nlp/extractor.py
│   ├── scraper/catalogue.py
│   ├── scraper/sources.py
│   └── services/search.py
├── data/                 # SQLite database is created here
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── .env.example
├── requirements.txt
└── README.md
```

## Search flow

1. User submits a natural-language requirement.
2. Gemini API with Google Search grounding suggests real product/supplier URLs.
3. The scraper fetches each accessible page and parses JSON-LD Product data, metadata, price hints, and specification tables.
4. NLP extracts basic budget, quantity, category hints, and specifications.
5. TF-IDF + Logistic Regression classifies each extracted product; a transparent relevance score ranks candidates.
6. Top matches and source URLs are shown. If the user is logged in, the extracted snapshot is automatically saved in their account history.

Direct URL mode skips discovery and scrapes the supplied page.

## API endpoints

- `POST /api/register` — individual or organization registration
- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`
- `POST /api/search` — `{ "query": "..." }` or `{ "url": "https://..." }`
- `GET /api/history` — authenticated
- `GET /api/history/<id>` — authenticated, owner-scoped
- `DELETE /api/history/<id>` — authenticated, owner-scoped
- `DELETE /api/history` — authenticated, clears own history
- `GET /health`

## Current MVP limits / next steps

- Browser-based JavaScript product pages may need a site-specific adapter or a permitted browser renderer.
- Gemini model access, grounding availability and quotas depend on your Google AI Studio project and selected model. If grounding is unavailable, the UI will show a discovery error; direct URL extraction remains available.
- Password reset, email verification, CSRF protection, rate limiting, production deployment configuration, and organization team/multi-member permissions are not implemented in this time-boxed MVP.
- `data/smartprocure.db` is created automatically on first run. Do not commit this file.
