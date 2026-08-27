# Phase notes (preserved)

## Phase 0 — Foundations
Data modelling for people, documents and tasks; Python OOP structure; log analysis.
Carried forward as typed Pydantic contracts (`app/models/schemas.py`) shared by the API,
the agent tools and both frontends, so a schema change breaks in one place.

## Phase 1 — Dashboards and APIs
Streamlit admin surfaces over FastAPI REST endpoints. Carried forward as eight pages
(Overview, Chat, People, Documents, Policy Search, Workflows, Analytics, Audit, Settings)
sharing one theme module and one API client.

## Phase 2 — System memory
Mongo for operational records, Supabase pgvector for semantic memory, Celery for async.
Carried forward with a repository facade so the same code path works against Mongo or an
in-process store — which is what makes the agent tools unit-testable.

## Phase 3 — AI core
Gemini function calling. Carried forward as a bounded tool loop (max 6 steps) with a
declaration registry, per-call timing, and a rule-based planner that runs the same tools
when no API key is present.

## Phase 4 — Security and deployment
Firebase bearer verification with role claims and a loud dev bypass; n8n webhook
forwarding; Playwright browser tasks; multi-stage Dockerfile with api / worker / ui
targets and a compose file wiring Redis.
