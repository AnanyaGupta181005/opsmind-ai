"""OpsMind AI — FastAPI orchestrator.

Boots with zero credentials: each subsystem reports live/mock at /health, so a
reviewer can see exactly what is real without reading the source.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import (
    routes_agent,
    routes_audit,
    routes_documents,
    routes_employees,
    routes_rag,
    routes_tasks,
)
from app.config import settings
from app.db.mongo import db
from app.rag.store import store
from app.security.auth import auth_mode
from app.workers.celery_app import broker_available

app = FastAPI(
    title="OpsMind AI",
    version=__version__,
    description="Natural-language operations orchestrator: agent, RAG, people ops.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (
    routes_agent.router,
    routes_employees.router,
    routes_documents.router,
    routes_rag.router,
    routes_tasks.router,
    routes_audit.router,
):
    app.include_router(r)

STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/console", include_in_schema=False)
async def console():
    """The operator chat UI, served by the API itself."""
    return FileResponse(STATIC / "index.html")


@app.get("/health", tags=["meta"])
async def health():
    return {
        "status": "ok",
        "version": __version__,
        "env": settings.app_env,
        "auth_mode": auth_mode(),
        "capabilities": settings.capability_report(),
        "datastore": {"mongo_reachable": await db.ping(), "mode": db.mode},
        "vector_store": store.stats(),
        "celery_broker": broker_available(),
        "model": settings.gemini_model if settings.has_gemini else "rule-planner (mock)",
    }


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse(STATIC / "index.html")
