# Phase-wise notes

The original build was organised as PHASE 0–4 learning milestones. The application code
now lives in one clean tree (`app/`, `ui/`, `tests/`); these notes record what each phase
covered and where that work ended up.

| Phase | Focus | Where it lives now |
|---|---|---|
| 0 | Foundations, data modelling, log analysis | `app/models/schemas.py`, `app/db/mongo.py` |
| 1 | Admin dashboards + REST APIs | `ui/`, `app/api/` |
| 2 | System memory + async workers | `app/rag/`, `app/workers/` |
| 3 | AI core and Manager Agent | `app/agent/` |
| 4 | Security, n8n workflows, deployment | `app/security/`, `app/api/routes_tasks.py`, `Dockerfile` |

## What changed in the rebuild

- **One app, not five phase folders.** Same concepts, one import graph, one test suite.
- **RAG is real and it is a tool.** Chunk → embed → store → retrieve → cite, and the agent
  is forced through it for policy questions instead of answering from model memory.
- **Every subsystem degrades instead of crashing.** `/health` reports live vs mock per
  subsystem, so the project demos with no credentials at all.
- **Writes are governed.** Write tools are withheld from the model unless the session arms
  them, and every write is audited.
