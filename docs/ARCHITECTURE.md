# NextLeap RAG Chatbot — Phase-wise Architecture

**Version:** 1.0  
**Scope:** Architecture only (deployment excluded; to be added later)

---

## 1. Executive Summary

This document defines a **phase-wise architecture** for a RAG (Retrieval-Augmented Generation) chatbot that answers user questions about **NextLeap** programs—courses, duration, hours, instructors, fees, placement, and related topics. The system will use data from **https://nextleap.app/** and a **structured reference knowledge base** to build a searchable corpus, serve answers via a retrieval-augmented LLM, expose a **frontend and backend** for the chat application, and use a **scheduler** to refresh data and RAG indices so the system always has the latest information.

**Out of scope for this architecture:** Deployment, DevOps, and production infrastructure.

---

## 2. Phase Overview

| Phase | Name | Objective |
|-------|------|------------|
| **Phase 1** | Data Ingestion | Fetch and structure data from nextleap.app for all cohorts (courses, hours, instructors, etc.) and persist for RAG. |
| **Phase 2** | RAG Pipeline | Ingest structured data → chunk → embed → index in a vector store; define retrieval and ranking. |
| **Phase 3** | Chatbot Service | Core chat logic: query → retrieval → LLM → response; prompt templates and context formatting. |
| **Phase 4** | Frontend & Backend | Backend API (HTTP/WebSocket) for the chat application; frontend chat UI (messages, input, sources). |
| **Phase 5** | Data Refresh Scheduler | Run Phase 1 on a schedule, then trigger Phase 2 (and downstream) so the system always uses the latest data. |

Deployment (hosting, CI/CD, monitoring) will be designed and documented in a later phase.

---

## 3. Phase 1 — Data Ingestion from nextleap.app

### 3.1 Objectives

- **Source:** https://nextleap.app/
- **Cohorts in scope:**
  1. **Product Management** (Product Manager Fellowship)
  2. **UX Design** (UI/UX Designer Fellowship)
  3. **Data Analytics** (Data Analyst Fellowship)
  4. **Business Analytics** (Business Analyst Fellowship)
  5. **GenAI Bootcamp**

- **Data to capture (per cohort / course):**
  - Course/program name and description
  - Duration (e.g. 16 weeks)
  - Weekly commitment / total hours (e.g. 14–15 hrs/week, 100+ live hours)
  - Instructors / mentors (names, roles if available)
  - Curriculum / topics / skills / tools
  - Fees, EMI (e.g. ₹39,999, EMI from ₹1322/month)
  - Schedule (e.g. Saturday/Sunday/Thursday slots)
  - Placement support, career outcomes, hiring network
  - Any cohort-specific features (e.g. Figma sessions, AI tools)

User questions will center on: **courses, hours, instructors**, plus fees, curriculum, schedule, and outcomes—so the ingestion pipeline must capture these fields explicitly.

### 3.2 Data Sources Strategy

Two complementary sources:

1. **Reference structured knowledge base**  
   - Use the provided JSON-like structured data (platform overview, features, fellowship programs, schedule, career support, outcomes, example Q&A) as the **authoritative seed** for:
     - Platform description, features, intents
     - Per-cohort: course name, duration, fees, curriculum, projects, tools, outcomes
   - Store as normalized JSON (and/or markdown) in the repo under something like `data/reference/` or `knowledge_base/`.

2. **Live data from nextleap.app**  
   - **Scrape** nextleap.app to:
     - Fill in **instructors** (names/roles) if present on the site
     - Get **exact hours** (e.g. “14–15 hours/week”, “100+ live hours”) where visible
     - Refresh **course names**, **fees**, **duration**, **schedule** if they differ from reference
     - Add **GenAI Bootcamp** and any new cohorts not in the reference set
   - The site appears to be **client-rendered (SPA)**; static HTTP fetch may not get full content. Options:
     - **Headless browser (Playwright / Puppeteer)** to render JS and extract text/HTML.
     - If NextLeap exposes a **public API or sitemap**, use that for stable, structured ingestion.
   - Scraped output should be **normalized** into the same schema as the reference data so downstream RAG sees one consistent structure.

### 3.3 Target Cohorts and Data Mapping

| Cohort | Reference name / slug | Data to fetch from site |
|--------|------------------------|--------------------------|
| Product Management | Product Manager Fellowship | Duration, weekly hours, curriculum, fees, EMI, instructors, schedule, projects |
| UX Design | UI/UX Designer Fellowship | Duration, skills, tools, fees, instructors, Figma/special sessions |
| Data Analytics | Data Analyst Fellowship | Duration, skills, projects, fees, placement, instructors |
| Business Analytics | Business Analyst Fellowship | Target roles, tools, curriculum, instructors (reference has no duration/fees; scrape if present) |
| GenAI Bootcamp | GenAI Bootcamp | All available: name, duration, hours, instructors, curriculum, fees (primarily from scrape) |

Instructors are called out explicitly because users will ask “Who teaches?”—so the pipeline must have a dedicated field (e.g. `instructors: [{ name, role }]`) per program.

### 3.4 Technical Approach for Phase 1

- **Reference data**
  - Manually curated JSON/Markdown files under version control.
  - Schema: one file per cohort plus platform-level (overview, features, schedule, career support, outcomes).
  - Optional: script to validate reference JSON against a schema.

- **Scraper (nextleap.app)**
  - **Tool:** Playwright (or Puppeteer) for SPA.
  - **URLs:** Start from homepage; discover cohort/course pages via links (e.g. `/courses`, `/product-management`, `/ux-design`, `/data-analytics`, `/business-analytics`, `/genai` or similar). Sitemap if available.
  - **Extraction:** Parse rendered DOM for:
    - Headings and sections (course name, duration, hours, schedule)
    - Tables or lists (curriculum, tools, instructors)
    - Fee/EMI text (regex or structured blocks)
  - **Output:** JSON per cohort/course matching the reference schema (e.g. `data/scraped/product_management.json`). Include `instructors`, `hours`, `duration`, `fee`, `schedule`, etc.
  - **Idempotent runs:** Overwrite or version scraped files; optional “last_updated” in JSON.

- **Merge / canonical dataset**
  - **Merge step:** Combine reference + scraped:
    - Prefer scraped for: instructors, exact hours, current fees, schedule.
    - Prefer reference for: rich curriculum lists, outcomes, platform narrative, example Q&A.
  - **Output:** Single **canonical knowledge set** (e.g. `data/canonical/`) used as the only input to Phase 2. Format: JSON (and/or Markdown) with a clear schema.

### 3.5 Schema (Phase 1 — Canonical Program/Cohort)

Suggested minimal structure for each cohort/program document:

```json
{
  "cohort_id": "product_manager_fellowship",
  "name": "Product Manager Fellowship",
  "slug": "product-management",
  "duration_weeks": 16,
  "weekly_hours": { "min": 14, "max": 15 },
  "total_live_hours": "100+",
  "instructors": [
    { "name": "...", "role": "Lead Instructor" }
  ],
  "curriculum_topics": [],
  "tools_taught": [],
  "fee": "₹39,999",
  "emi_starting": "₹1322/month",
  "schedule": { "saturday": [], "sunday": [], "thursday": [] },
  "placement_support": "...",
  "target_roles": [],
  "source": "reference|scraped|merged",
  "last_updated": "ISO8601"
}
```

Platform-level documents (overview, features, schedule template, career support, outcomes) can stay separate with their own small schemas.

### 3.6 Suggested Repository Layout (Phase 1)

```
data/
  reference/          # Curated JSON/MD from your structured knowledge base
    platform.json
    product_management.json
    ux_design.json
    data_analytics.json
    business_analytics.json
    genai_bootcamp.json
    schedule.json
    career_support.json
  scraped/            # Output of nextleap.app scraper (per cohort)
  canonical/          # Merged reference + scraped (input to Phase 2)
scripts/ or src/
  scrape/             # Playwright scraper, URL discovery, extractors
  merge/              # Reference + scraped → canonical
  validate/           # Schema validation for canonical data
```

### 3.7 Phase 1 Deliverables

- [ ] Reference knowledge base (JSON/MD) in repo for all 5 cohorts + platform.
- [ ] Scraper (Playwright) that hits nextleap.app and extracts courses, hours, instructors, fees, schedule.
- [ ] Normalized scraped JSON per cohort.
- [ ] Merge logic: reference + scraped → canonical dataset.
- [ ] Schema (and optional validation) for canonical data.
- [ ] Readme in `data/` or `docs/` describing how to run the scraper and regenerate canonical data.

**Note on nextleap.app:** The site appears to be a client-rendered SPA; server-side fetch returns minimal HTML. Use a headless browser (e.g. Playwright) to render pages and extract course details, instructor names, and hours. If NextLeap adds a sitemap or public API later, the scraper can be updated to use those for more stable ingestion.

---

## 4. Phase 2 — RAG Pipeline

### 4.1 Objectives

- Ingest the **canonical knowledge set** from Phase 1.
- Chunk text for retrieval (by section, by cohort, or hybrid).
- Embed chunks with a chosen embedding model.
- Store embeddings in a **vector store** and support similarity search.
- Expose a **retrieval API** (query → top-k chunks + optional metadata).

### 4.2 Pipeline Stages

1. **Load**  
   Read canonical JSON/MD; optionally convert JSON to readable text (e.g. “Product Manager Fellowship: 16 weeks, 14–15 hrs/week…”).

2. **Chunking**  
   - Strategy: semantic boundaries (e.g. per cohort, per section: curriculum, fees, instructors, schedule).
   - Chunk size: e.g. 256–512 tokens with overlap; keep “instructors” and “hours” in coherent chunks.
   - Metadata: attach `cohort_id`, `section` (e.g. curriculum, fees, instructors) for filtering.

3. **Embedding**  
   - Model: e.g. OpenAI `text-embedding-3-small`, or open-source (sentence-transformers, etc.).
   - Input: chunk text + optional metadata concatenation for better retrieval.

4. **Vector store**  
   - Options: Chroma, Qdrant, Weaviate, Pinecone, or in-memory for dev.
   - Index: embedding + metadata (cohort_id, section) for filtered retrieval.

5. **Retrieval**  
   - Query: user question → same embedding model → vector search.
   - Return: top-k chunks (e.g. k=5–10); optional pre-filter by cohort if detected from query.
   - Optional: reranker for better precision.

### 4.3 Phase 2 Deliverables

- [ ] Loader from canonical data to documents/chunks.
- [ ] Chunking logic and metadata attachment.
- [ ] Embedding integration and vector index build.
- [ ] Retrieval function (query → top-k chunks).
- [ ] Config for chunk size, model, k (no deployment yet).

---

## 5. Phase 3 — Chatbot Service

### 5.1 Objectives

- Provide a **chat API** that accepts a user message and returns an answer.
- Flow: user query → retrieval (Phase 2) → build context from chunks → **LLM (Groq)** → response.
- Support intents: “What is NextLeap?”, “Courses offered”, “Course duration”, “Fees and EMI”, “Placement support”, “Eligibility”, “Curriculum”, “Schedule”, “Tools taught”, “Career outcomes”, **“Instructors”**, **“Hours”**.

**LLM:** Phase 3 uses **Groq** as the LLM provider for response generation (e.g. Groq-hosted Llama or other supported models). Config must include Groq API key and model name.

### 5.2 Answering policy (grounding and scope)

- **Retrieval-only answers:** The chatbot **must not answer from its own knowledge**. Every answer must be based **only** on information retrieved from the embeddings (Phase 2). If the retrieved context does not contain enough information to answer the question, the chatbot should say so (e.g. “I don’t have that information in my knowledge base”) and not invent or infer an answer.
- **Out-of-scope: personal information.** Questions asking for **personal information** (e.g. about specific individuals, contact details, private data) are **out of scope**. The chatbot must decline to answer such questions and state that they are outside the scope of the NextLeap course/fellowship information it can provide.

### 5.3 Query Flow

1. **Receive** user message.
2. **Retrieve** top-k relevant chunks (Phase 2).
3. **Build prompt:** system message (e.g. “You are the NextLeap chatbot. Answer only using the provided context…”) + retrieved context + user question.
4. **LLM (Groq)** generates answer **strictly grounded in the provided context**; do not answer from general knowledge.
5. **Return** answer (and optionally cited chunks/sources and source URL).
6. **Out-of-scope check:** If the query is about personal information, return a polite out-of-scope message instead of using context or LLM for that content.

### 5.4 API Shape (Conceptual)

### 5.3 API Shape (Conceptual)

- `POST /chat` or `POST /query`  
  - Body: `{ "message": "Who teaches the Product Management course?" }`  
  - Response: `{ "answer": "...", "sources": [ { "cohort_id", "text_snippet", "source_url" } ] }`

### 5.5 Phase 3 Deliverables

- [ ] Chat/query service (retrieval + Groq LLM) callable by Phase 4 backend.
- [ ] Prompt template that enforces **answer only from provided context**; no general-knowledge or self-generated answers.
- [ ] Out-of-scope handling for personal-information and other off-topic queries.
- [ ] Config for Groq API key and model.

---

## 6. Phase 4 — Frontend & Backend (Chat Application)

### 6.1 Objectives

- **Backend:** Expose the chat application’s API (REST or WebSocket) that consumes the Chatbot Service (Phase 3), handles sessions, errors, and optional rate limiting.
- **Frontend:** Provide a chat UI where users can send messages, see answers, and (optionally) view cited sources—responsive and usable across devices.

Together, Phase 4 delivers the **full chat application** (server + client) that end users interact with.

### 6.2 Backend

- **API surface:**
  - `POST /chat` or `POST /query`: body `{ "message": "..." }` (and optional `session_id`, `conversation_id`); returns `{ "answer": "...", "sources": [...] }`.
  - Optional: `GET /health`, `GET /api/status` for liveness and “last data refresh” (from Phase 5).
- **Responsibilities:**
  - Call Phase 3 (retrieval + LLM) for each user message.
  - Session/conversation handling (in-memory or persistent) so multi-turn context can be used if needed.
  - Error handling (e.g. LLM timeout, empty retrieval) and consistent error response shape.
  - Optional: request validation, API key or auth (if required later).
- **Technology:** FastAPI or Flask; can run in the same process as Phase 3 or as a separate service that calls it.

### 6.3 Frontend

- **Features:**
  - Chat layout: message list (user + assistant), input box, send button.
  - Display assistant answers and optional source citations (e.g. cohort name, snippet).
  - Loading state while the backend is processing.
  - Basic accessibility (keyboard, focus, labels) and responsive layout (mobile/desktop).
- **Stack (suggestions):** React, Next.js, or Vue; or a simple static HTML/JS page that calls the backend. Styling: CSS/Tailwind; optional component library.
- **Integration:** Frontend calls the Phase 4 backend (e.g. `POST /chat`); no direct dependency on vector store or Phase 2.

### 6.4 Phase 4 Deliverables

- [ ] Backend API server (HTTP/WebSocket) that delegates to Phase 3 and returns structured responses.
- [ ] Frontend chat UI (messages, input, send, optional sources).
- [ ] Session/conversation handling and error responses.
- [ ] Readme or doc for running backend + frontend locally.

---

## 7. Phase 5 — Data Refresh Scheduler

### 7.1 Objectives

- Run **Phase 1** (data ingestion from nextleap.app + merge → canonical dataset) on a **schedule** (e.g. daily or weekly).
- After Phase 1 completes successfully, **trigger Phase 2** (RAG pipeline: re-chunk, re-embed, rebuild vector index) so the chatbot uses the latest canonical data.
- Optionally signal or restart components (e.g. reload index in Phase 3/4) so the **entire system** reflects the latest data on every run.

Goal: **latest data every time** without manual re-runs.

### 7.2 Scheduler Flow

1. **Trigger** (cron, systemd timer, or workflow orchestrator) at configured intervals (e.g. `0 2 * * *` for 2 AM daily).
2. **Run Phase 1:**
   - Execute scraper for nextleap.app.
   - Run merge: reference + scraped → canonical dataset.
   - Write outputs to `data/canonical/` (and optionally `data/scraped/`).
3. **Trigger Phase 2:**
   - Run RAG pipeline: load canonical data → chunk → embed → rebuild vector store (full reindex or incremental if supported).
   - Ensure Phase 3 (and thus Phase 4) use this updated store on the next request (e.g. same process reads from disk, or vector DB is updated in place).
4. **Optional:**
   - Emit event or call webhook to reload in-memory caches.
   - Write “last_updated” timestamp (e.g. to a file or DB) so Phase 4 backend can expose “Data last refreshed at …” in `/health` or `/api/status`.
   - On failure: alert (e.g. log + optional notification); do not trigger Phase 2 if Phase 1 failed.

### 7.3 Implementation Options

- **Cron + scripts:** Shell script that runs `python -m scripts.run_phase1`, then `python -m scripts.run_phase2`; cron invokes the script.
- **Task queue:** Celery, Redis Queue, or similar: scheduled task runs Phase 1, on success enqueues Phase 2 job.
- **Workflow orchestrator:** Prefect, Airflow, or Dagster: DAG “Data Refresh” with node 1 = Phase 1, node 2 = Phase 2 (depends on 1).
- **In-process scheduler:** APScheduler inside the backend app (simpler, but less robust for heavy scrapes); good for demos.

### 7.4 Phase 5 Deliverables

- [ ] Scheduled job that runs Phase 1 (scrape + merge → canonical).
- [ ] Automatic trigger of Phase 2 (rebuild RAG index) after Phase 1 success.
- [ ] Configuration for schedule (e.g. cron expression or interval).
- [ ] Optional: “last_updated” exposed to backend/health endpoint; failure handling and alerts.

---

## 8. Data Flow Summary

```
Phase 1:
  nextleap.app (scrape) + reference JSON
    → Scraper + Merge
    → Canonical dataset (courses, hours, instructors, fees, curriculum, etc.)

Phase 2:
  Canonical dataset
    → Chunk + Embed
    → Vector store
    → Retrieval (query → top-k chunks)

Phase 3:
  User message
    → Retrieval
    → LLM + context
    → Answer (+ optional sources)

Phase 4:
  User (browser)
    → Frontend (chat UI)
    → Backend API (POST /chat)
    → Phase 3 (chatbot service)
    → Response to user

Phase 5 (scheduled):
  Scheduler trigger (e.g. cron)
    → Phase 1 (refresh canonical data)
    → Phase 2 (rebuild vector index)
    → Phase 3/4 use updated index on next request
```

---

## 9. Technology Suggestions (Non-binding)

- **Phase 1:** Python 3.10+; Playwright; pydantic for schema/validation.
- **Phase 2:** LangChain/LlamaIndex or minimal custom code; sentence-transformers or OpenAI embeddings; Chroma/Qdrant for vectors.
- **Phase 3:** Python; **Groq** as LLM (Groq API key required); prompt templates that restrict answers to retrieved context only; out-of-scope handling for personal information.
- **Phase 4:** Backend: FastAPI or Flask; Frontend: React / Next.js / Vue or static HTML+JS; Tailwind or similar for styling.
- **Phase 5:** Cron + shell scripts; or Celery/Prefect/Airflow/APScheduler for orchestration.

---

## 10. Out of Scope (For Later)

- Deployment (hosting, containers, CI/CD).
- Production monitoring, logging, rate limiting.
- Authentication and multi-tenancy.
- Feedback loop (thumbs up/down, retrieval quality metrics).

**Chatbot must not do:** Answer from its own/general knowledge; answer questions about **personal information** (individuals, contact details, private data)—treat these as out of scope and decline politely.

---

## 11. Reference: Intent Categories for Chatbot

Align retrieval and prompts with these intents:

- What is NextLeap?
- Courses offered (including GenAI Bootcamp)
- Course duration
- Fees and EMI
- Placement support
- Eligibility
- Curriculum
- Schedule
- Tools taught
- Career outcomes
- **Instructors** (who teaches which cohort)
- **Hours** (weekly/total commitment)

Phase 1 must ensure **instructors** and **hours** are present in the canonical data so that Phase 2 and 3 can answer those questions accurately.

---

*Document end. Deployment and operations will be covered in a separate architecture phase.*
