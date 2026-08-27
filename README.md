# OpsMind AI · Intelligent Management Orchestrator

OpsMind AI turns plain-English operational requests into executed work. It is not a
chatbot wrapper: a Gemini function-calling agent decides which tool to run, runs it
against real data, and reports what it did — every tool call and every retrieved
passage is shown in the UI.

> Rebuilt end to end: one clean application, a working RAG pipeline, two frontends,
> and a stack that boots and demos with **zero credentials**.

---

## What it does

| Capability | How it works |
|---|---|
| **Natural-language people ops** | "Find all interns who joined last month" → the agent converts the relative date to ISO, calls `search_employees`, and reports the matches. |
| **Policy RAG with citations** | Handbooks and SOPs are chunked, embedded and searched by cosine similarity; answers cite `[n]` passages and refuse when evidence is weak. |
| **Document intelligence** | PDF text extraction plus Gemini Vision structured parsing of invoices and resumes into fixed JSON schemas. |
| **Agentic workflows** | Report generation on Celery, browser tasks on Playwright, external orchestration via n8n webhooks. |
| **Governed writes** | Write tools are hidden from the model unless the session arms them; every write lands in the audit log. |

## Architecture

```
                    ┌─────────────────────────┐
  Operator console  │  /console  (HTML + JS)  │  served by FastAPI
  Admin console     │  Streamlit (8 pages)    │  :8501
                    └───────────┬─────────────┘
                                │ REST
                    ┌───────────▼─────────────┐
                    │   FastAPI orchestrator  │  :8000
                    │  agent · rag · people   │
                    │  documents · tasks      │
                    └──┬─────────┬─────────┬──┘
                       │         │         │
        ┌──────────────▼──┐  ┌───▼────┐  ┌─▼──────────────┐
        │ Gemini          │  │ Mongo  │  │ Supabase       │
        │ tools+embed+    │  │ ops    │  │ pgvector       │
        │ vision          │  │ data   │  │ policy_chunks  │
        └─────────────────┘  └────────┘  └────────────────┘
                       │
              ┌────────▼────────┐
              │ Celery + Redis  │  reports, reindexing
              │ Playwright, n8n │  web + external workflows
              └─────────────────┘
```

### The RAG pipeline

1. **Ingest** — `/documents/upload` extracts text (pypdf for PDFs).
2. **Chunk** — `app/rag/chunking.py` splits paragraph-first at ~900 chars with 150 chars of
   tail overlap, so a policy clause is rarely cut in half.
3. **Embed** — Gemini `text-embedding-004` (768-d). No key? a deterministic local
   embedder keeps retrieval working for demos.
4. **Store** — Supabase `policy_chunks` with an ivfflat cosine index and a
   `match_policy_chunks` RPC (`sql/supabase_schema.sql`). No key? an in-process index.
5. **Retrieve + generate** — top-k above `RAG_MIN_SCORE`, then a grounded answer that
   must cite its passages and must say so when the handbook does not cover the question.
6. **Expose** — RAG is also an agent tool (`search_policy`), and the system prompt forces
   every policy question through it rather than through model memory.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env                                  # optional — it runs empty
python -m scripts.seed                                # index the sample handbook
uvicorn app.main:app --reload                         # API + operator console
streamlit run ui/streamlit_app.py                     # admin console
```

- Operator chat console — http://localhost:8000/console
- API docs — http://localhost:8000/docs
- Capability report — http://localhost:8000/health
- Admin console — http://localhost:8501

Docker: `docker compose up --build` (api, worker, redis, ui).

### Mock mode is a feature

Every subsystem degrades instead of crashing, and `/health` reports exactly which are
live. The UI shows a **live** or **mock** badge per subsystem, so a reviewer can see what
is real without reading the source. Add a key, restart, and the badge flips.

## Layout

```
app/
  main.py               FastAPI app, /health capability report, /console
  config.py             settings + capability flags
  api/                  employees · documents · rag · agent · tasks · audit
  agent/                tool registry, declarations, Gemini function-calling loop
  rag/                  chunking · embeddings · vector store · answer pipeline
  services/             ocr (Gemini Vision) · reports · web_tasks (Playwright)
  workers/               celery app + tasks with inline fallback
  security/             Firebase bearer auth + dev bypass
  static/index.html     operator console (chat + Team/Handbook/Reports/Activity)
ui/                     Streamlit admin console (8 pages) + shared theme
sql/                    Supabase pgvector schema and retrieval RPC
scripts/seed.py         seeds a sample handbook and SOP into the index
tests/                  RAG and agent-tool tests
docs/phases/            phase-wise learning notes from the original build
```

## Tests

```bash
pytest
```

Covers chunking, retrieval ranking, refusal on empty evidence, tool filtering for
read-only sessions, and the agent routing policy questions through RAG.

## Environment

See `.env.example`. Nothing is required; each key upgrades one subsystem from mock to live.

---

*Developed as part of the InBenne Internship Program by Ananya Gupta.*
