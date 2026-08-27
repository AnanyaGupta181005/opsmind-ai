"""The agent's hands.

Every tool is a plain async python function with a JSON-schema declaration.
Write tools are gated behind `allow_writes` at the orchestrator level, so a
read-only session can never mutate the org.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from app.db.mongo import db, to_employee
from app.rag.pipeline import answer as rag_answer
from app.rag.store import store

WRITE_TOOLS = {"create_employee", "deactivate_employee", "queue_report"}


# --------------------------------------------------------------------- reads
async def search_employees(
    role: str | None = None,
    department: str | None = None,
    joined_after: str | None = None,
    joined_before: str | None = None,
    active: bool | None = None,
    limit: int = 25,
) -> dict:
    flt: dict[str, Any] = {}
    if role:
        flt["role"] = role
    if department:
        flt["department"] = department
    if active is not None:
        flt["active"] = active
    if joined_after or joined_before:
        rng: dict[str, str] = {}
        if joined_after:
            rng["$gte"] = joined_after
        if joined_before:
            rng["$lte"] = joined_before
        flt["joined_on"] = rng

    docs = await db.col("employees").find(flt, limit=limit)
    people = [to_employee(d) for d in docs]
    return {"count": len(people), "employees": people, "filter": flt}


async def headcount_by(dimension: str = "department") -> dict:
    docs = await db.col("employees").find({}, limit=10_000)
    buckets: dict[str, int] = {}
    for d in docs:
        key = str(d.get(dimension, "unknown"))
        buckets[key] = buckets.get(key, 0) + 1
    return {"dimension": dimension, "buckets": buckets, "total": len(docs)}


async def search_policy(question: str, top_k: int = 5) -> dict:
    """RAG lookup over the indexed handbook set."""
    return rag_answer(question, top_k=top_k)


async def list_documents(kind: str | None = None) -> dict:
    flt = {"kind": kind} if kind else {}
    docs = await db.col("documents").find(flt, limit=200)
    return {
        "count": len(docs),
        "documents": [
            {
                "id": str(d.get("_id")),
                "title": d.get("title"),
                "kind": d.get("kind"),
                "chunks": d.get("chunks", 0),
                "indexed": d.get("indexed", False),
            }
            for d in docs
        ],
        "index": store.stats(),
    }


# -------------------------------------------------------------------- writes
async def create_employee(
    name: str,
    email: str,
    role: str = "intern",
    department: str = "unassigned",
    joined_on: str | None = None,
    manager_email: str | None = None,
) -> dict:
    existing = await db.col("employees").find_one({"email": email})
    if existing:
        return {"ok": False, "reason": "email already exists", "id": str(existing["_id"])}
    doc = {
        "name": name,
        "email": email,
        "role": role,
        "department": department,
        "joined_on": joined_on or date.today().isoformat(),
        "manager_email": manager_email,
        "active": True,
    }
    _id = await db.col("employees").insert_one(doc)
    await db.audit("agent", "create_employee", {"email": email})
    return {"ok": True, "id": str(_id), "employee": to_employee({**doc, "_id": _id})}


async def deactivate_employee(email: str) -> dict:
    n = await db.col("employees").update_one({"email": email}, {"active": False})
    await db.audit("agent", "deactivate_employee", {"email": email})
    return {"ok": bool(n), "email": email, "modified": n}


async def queue_report(report: str = "headcount", period: str = "month") -> dict:
    """Hands work to Celery; falls back to inline execution without a broker."""
    from app.workers.tasks import submit_report

    return await submit_report(report=report, period=period)


# --------------------------------------------------------------- declarations
REGISTRY = {
    "search_employees": search_employees,
    "headcount_by": headcount_by,
    "search_policy": search_policy,
    "list_documents": list_documents,
    "create_employee": create_employee,
    "deactivate_employee": deactivate_employee,
    "queue_report": queue_report,
}

DECLARATIONS = [
    {
        "name": "search_employees",
        "description": "Find employees by role, department, join-date window or active flag. "
                       "Use for questions like 'interns who joined last month'.",
        "parameters": {
            "type": "object",
            "properties": {
                "role": {"type": "string", "enum": ["intern", "engineer", "manager", "admin"]},
                "department": {"type": "string"},
                "joined_after": {"type": "string", "description": "ISO date, inclusive"},
                "joined_before": {"type": "string", "description": "ISO date, inclusive"},
                "active": {"type": "boolean"},
                "limit": {"type": "integer"},
            },
        },
    },
    {
        "name": "headcount_by",
        "description": "Aggregate headcount by a dimension (department, role).",
        "parameters": {
            "type": "object",
            "properties": {"dimension": {"type": "string"}},
        },
    },
    {
        "name": "search_policy",
        "description": "Answer any question about company policy, handbook, leave, "
                       "reimbursement or SOPs using retrieval over indexed documents. "
                       "Always prefer this over answering policy from memory.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string"},
                "top_k": {"type": "integer"},
            },
            "required": ["question"],
        },
    },
    {
        "name": "list_documents",
        "description": "List documents known to the system and index statistics.",
        "parameters": {"type": "object", "properties": {"kind": {"type": "string"}}},
    },
    {
        "name": "create_employee",
        "description": "Onboard a new person. Requires write permission.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "role": {"type": "string"},
                "department": {"type": "string"},
                "joined_on": {"type": "string"},
                "manager_email": {"type": "string"},
            },
            "required": ["name", "email"],
        },
    },
    {
        "name": "deactivate_employee",
        "description": "Offboard a person by email. Requires write permission.",
        "parameters": {
            "type": "object",
            "properties": {"email": {"type": "string"}},
            "required": ["email"],
        },
    },
    {
        "name": "queue_report",
        "description": "Queue a background report generation job. Requires write permission.",
        "parameters": {
            "type": "object",
            "properties": {"report": {"type": "string"}, "period": {"type": "string"}},
        },
    },
]


def declarations_for(allow_writes: bool) -> list[dict]:
    if allow_writes:
        return DECLARATIONS
    return [d for d in DECLARATIONS if d["name"] not in WRITE_TOOLS]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
