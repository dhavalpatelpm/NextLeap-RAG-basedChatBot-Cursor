# NextLeap RAG Chatbot

RAG-based chatbot for NextLeap courses (Product Management, UX Design, Data Analytics, Business Analytics, GenAI Bootcamp). Architecture is in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Phase 1 — Data ingestion

Phase 1 scrapes course pages from **https://nextleap.app/course/...** and merges with curated reference data into a canonical dataset used by later phases.

### Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

### Run

```bash
# Scrape all cohorts and merge to canonical
python scripts/run_phase1.py

# Merge only (use existing data/scraped/)
python scripts/run_phase1.py --no-scrape

# Scrape only
python scripts/run_phase1.py --scrape-only

# One cohort
python scripts/run_phase1.py --cohorts product_management
```

### Data layout

| Directory      | Purpose |
|----------------|---------|
| `data/reference/` | Curated JSON per cohort (and `platform.json`). Edit to add curriculum, tools, narrative. |
| `data/scraped/`   | Scraper output (live prices, cohort dates, instructors, schedule, salary). |
| `data/canonical/` | Merged reference + scraped; input for Phase 2 (RAG). |

See [data/README.md](data/README.md) for details and course URLs.

### Important data captured (all cohorts)

- **100+ hours live classes**, **4 months** / fellowship timeline  
- **Mentorship** (e.g. with experienced PMs)  
- **Placement support** (e.g. 1 year), cut-off and partner companies  
- **Cohort** (e.g. Cohort 48 starts on Apr 4)  
- **Cost** (current/original), **EMI**, **price increase** info  
- **Live class schedule**  
- **Instructors** (Learn from our instructors)  
- **Salary** (average e.g. 14–18 Lakhs, highest e.g. 31 Lakhs)  

Reference data for Product Manager Fellowship is aligned with [nextleap.app/course/product-management-course](https://nextleap.app/course/product-management-course); other cohorts have baseline reference and are enriched by the scraper where the site provides the same structure.

## Running tests (Phase 3 integration)

Integration tests exercise the full flow: Phase 2 retrieval + Groq LLM. They require:

- **GROQ_API_KEY** in `.env` (see `.env.example`)
- **Phase 2 vector store** built: `python scripts/run_phase2.py`

Then run:

```bash
pip install -r requirements.txt   # includes pytest
pytest tests/test_phase3_integration.py -v
```

Example test case: query *"What is the price of product management fellowship?"* — tests assert the answer contains the price (e.g. 34999 or ₹34,999) and that the Product Manager Fellowship URL (`https://nextleap.app/course/product-management-course`) appears in the answer or in the returned sources.

## Phase 4 — Backend & Frontend (Chat application)

Backend (FastAPI) exposes `POST /chat` and serves the chat UI. Frontend is a single-page app with a dark theme and blue accents: header, left sidebar (suggested questions), main chat area (message bubbles, input, send button), and right sidebar (sources from the latest answer).

### Run the app

**Option A — Direct run (if `pip install` works on your machine):**

```bash
cd /path/to/NextLeap-RAG-basedChatBot-Cursor
pip install -r requirements.txt
python scripts/run_phase4.py
```

**Option B — Using a virtual environment (if you get "Operation not permitted" or permission errors):**

```bash
cd /path/to/NextLeap-RAG-basedChatBot-Cursor
bash scripts/run_server_with_venv.sh
```

This creates a `.venv` folder in the project, installs dependencies there, and starts the server. No system Python install needed.

**Then:** Open **http://127.0.0.1:8000** in your browser. Keep the terminal open while using the app.

**For chat to work:** You need Phase 2 vector store (`python scripts/run_phase2.py` once) and `.env` with `GROQ_API_KEY`. If those are missing, the UI still loads; sending a message will show an error until you set them up.

## Phase 5 — Data Refresh Scheduler

Phase 5 runs **Phase 1** (scrape + merge → canonical) then **syncs canonical to course_details** then **Phase 2** (rebuild RAG index). It writes a **last refresh** timestamp to `data/.last_refresh`, which the backend exposes as `data_last_refreshed_at` in **GET /api/status**.

**Manual refresh (recommended for cron):**

```bash
# Full refresh: scrape + merge + sync + rebuild RAG
python scripts/run_phase5_refresh.py

# Merge only (no scrape) + sync + rebuild RAG (e.g. after editing reference JSONs)
python scripts/run_phase5_refresh.py --no-scrape
```

**Optional: run refresh on a schedule (e.g. every 24h):**

```bash
pip install apscheduler   # or use requirements.txt
python scripts/run_phase5_scheduler.py --interval 24
```

**Cron example (daily at 2 AM):**  
`0 2 * * * cd /path/to/repo && .venv/bin/python scripts/run_phase5_refresh.py`
