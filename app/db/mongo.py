"""Mongo access with an in-memory fallback so the app never hard-fails.

The repository interface is identical in both modes, which is what makes the
agent's function-calling layer testable without a database.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from app.config import settings

_SEED = [
    {"name": "Ananya Gupta", "email": "ananya@inbenne.com", "role": "engineer",
     "department": "platform", "joined_on": "2025-06-02", "manager_email": "riya@inbenne.com"},
    {"name": "Riya Sharma", "email": "riya@inbenne.com", "role": "manager",
     "department": "platform", "joined_on": "2023-01-16", "manager_email": None},
    {"name": "Kabir Nair", "email": "kabir@inbenne.com", "role": "intern",
     "department": "data", "joined_on": "2026-07-14", "manager_email": "riya@inbenne.com"},
    {"name": "Meera Iyer", "email": "meera@inbenne.com", "role": "intern",
     "department": "design", "joined_on": "2026-07-28", "manager_email": "riya@inbenne.com"},
    {"name": "Dev Patel", "email": "dev@inbenne.com", "role": "engineer",
     "department": "infra", "joined_on": "2024-11-04", "manager_email": "riya@inbenne.com"},
    {"name": "Sana Qureshi", "email": "sana@inbenne.com", "role": "admin",
     "department": "operations", "joined_on": "2022-08-22", "manager_email": None},
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryCollection:
    """Minimal async-compatible stand-in for a Motor collection."""

    def __init__(self, docs: list[dict] | None = None):
        self._docs: list[dict] = []
        for d in docs or []:
            self._docs.append({"_id": str(uuid.uuid4()), **d})

    async def insert_one(self, doc: dict) -> str:
        _id = doc.get("_id") or str(uuid.uuid4())
        self._docs.append({**doc, "_id": _id})
        return _id

    async def find(self, flt: dict | None = None, limit: int = 200) -> list[dict]:
        return [d for d in self._docs if _matches(d, flt or {})][:limit]

    async def find_one(self, flt: dict) -> dict | None:
        hits = await self.find(flt, limit=1)
        return hits[0] if hits else None

    async def update_one(self, flt: dict, patch: dict) -> int:
        n = 0
        for d in self._docs:
            if _matches(d, flt):
                d.update(patch)
                n += 1
                break
        return n

    async def delete_one(self, flt: dict) -> int:
        for i, d in enumerate(self._docs):
            if _matches(d, flt):
                self._docs.pop(i)
                return 1
        return 0

    async def count(self, flt: dict | None = None) -> int:
        return len(await self.find(flt, limit=10**6))


def _matches(doc: dict, flt: dict) -> bool:
    for key, cond in flt.items():
        val = doc.get(key)
        if isinstance(cond, dict):
            for op, target in cond.items():
                if op == "$gte" and not (val is not None and str(val) >= str(target)):
                    return False
                if op == "$lte" and not (val is not None and str(val) <= str(target)):
                    return False
                if op == "$in" and val not in target:
                    return False
                if op == "$regex" and target.lower() not in str(val).lower():
                    return False
        elif val != cond:
            return False
    return True


class Database:
    """Facade over Motor or the in-memory store."""

    def __init__(self) -> None:
        self.mode = "mongo" if settings.has_mongo else "memory"
        self._client = None
        if self.mode == "mongo":
            from motor.motor_asyncio import AsyncIOMotorClient

            self._client = AsyncIOMotorClient(settings.mongo_uri, tz_aware=True)
            self._db = self._client[settings.mongo_db]
        else:
            self._mem = {
                "employees": MemoryCollection(_SEED),
                "documents": MemoryCollection(),
                "chat_turns": MemoryCollection(),
                "tasks": MemoryCollection(),
                "audit": MemoryCollection(),
            }

    # --- collection access -------------------------------------------------
    def col(self, name: str):
        if self.mode == "mongo":
            return _MotorAdapter(self._db[name])
        return self._mem[name]

    async def ping(self) -> bool:
        if self.mode == "mongo":
            try:
                await self._client.admin.command("ping")
                return True
            except Exception:
                return False
        return True

    async def audit(self, actor: str, action: str, payload: dict[str, Any] | None = None) -> None:
        await self.col("audit").insert_one(
            {"actor": actor, "action": action, "payload": payload or {}, "at": _now()}
        )


class _MotorAdapter:
    """Gives a Motor collection the same tiny surface as MemoryCollection."""

    def __init__(self, col):
        self._c = col

    async def insert_one(self, doc: dict) -> str:
        res = await self._c.insert_one(doc)
        return str(res.inserted_id)

    async def find(self, flt: dict | None = None, limit: int = 200) -> list[dict]:
        cur = self._c.find(flt or {}).limit(limit)
        out = []
        async for d in cur:
            d["_id"] = str(d["_id"])
            out.append(d)
        return out

    async def find_one(self, flt: dict) -> dict | None:
        d = await self._c.find_one(flt)
        if d:
            d["_id"] = str(d["_id"])
        return d

    async def update_one(self, flt: dict, patch: dict) -> int:
        res = await self._c.update_one(flt, {"$set": patch})
        return res.modified_count

    async def delete_one(self, flt: dict) -> int:
        res = await self._c.delete_one(flt)
        return res.deleted_count

    async def count(self, flt: dict | None = None) -> int:
        return await self._c.count_documents(flt or {})


db = Database()


def to_employee(doc: dict) -> dict:
    joined = doc.get("joined_on")
    if isinstance(joined, (datetime, date)):
        joined = joined.isoformat()[:10]
    return {
        "id": str(doc.get("_id")),
        "name": doc.get("name"),
        "email": doc.get("email"),
        "role": doc.get("role", "intern"),
        "department": doc.get("department", "unassigned"),
        "joined_on": joined,
        "manager_email": doc.get("manager_email"),
        "active": doc.get("active", True),
    }
