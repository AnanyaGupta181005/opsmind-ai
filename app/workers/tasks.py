"""Background jobs with a transparent inline fallback.

`submit_report` is the only entrypoint the agent and API touch; whether the
work landed on a Celery worker or ran inline is reported back, never hidden.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from app.db.mongo import db
from app.services.reports import headcount_report
from app.workers.celery_app import broker_available, celery_app

if celery_app is not None:

    @celery_app.task(name="opsmind.generate_report")
    def generate_report_task(report: str, period: str) -> dict:
        return asyncio.run(headcount_report(period))

    @celery_app.task(name="opsmind.reindex_document")
    def reindex_document_task(doc_id: str) -> dict:
        from app.rag.store import store

        return {"doc_id": doc_id, "index": store.stats()}


async def submit_report(report: str = "headcount", period: str = "month") -> dict:
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    if broker_available():
        async_res = generate_report_task.delay(report, period)
        await db.col("tasks").insert_one(
            {"_id": task_id, "kind": f"report:{report}", "state": "queued",
             "submitted_at": now, "detail": f"celery {async_res.id}", "celery_id": async_res.id}
        )
        return {"ok": True, "task_id": task_id, "runner": "celery", "state": "queued"}

    result = await headcount_report(period)
    await db.col("tasks").insert_one(
        {"_id": task_id, "kind": f"report:{report}", "state": "done",
         "submitted_at": now, "finished_at": datetime.now(timezone.utc),
         "detail": "ran inline (no broker)", "result": result}
    )
    return {"ok": True, "task_id": task_id, "runner": "inline", "state": "done",
            "result": result}


async def list_tasks(limit: int = 50) -> list[dict]:
    docs = await db.col("tasks").find({}, limit=limit)
    out = []
    for d in docs:
        out.append(
            {"id": str(d.get("_id")), "kind": d.get("kind"), "state": d.get("state"),
             "submitted_at": d.get("submitted_at"), "finished_at": d.get("finished_at"),
             "detail": d.get("detail"), "result": d.get("result")}
        )
    return out
