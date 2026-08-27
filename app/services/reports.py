"""Report generation used by both the API and Celery workers."""
from __future__ import annotations

from datetime import date, timedelta

from app.db.mongo import db, to_employee


async def headcount_report(period: str = "month") -> dict:
    docs = await db.col("employees").find({}, limit=10_000)
    people = [to_employee(d) for d in docs]

    today = date.today()
    window_start = (today.replace(day=1) if period == "month"
                    else today - timedelta(days=90))

    by_dept: dict[str, int] = {}
    by_role: dict[str, int] = {}
    joiners = []
    for p in people:
        by_dept[p["department"]] = by_dept.get(p["department"], 0) + 1
        by_role[p["role"]] = by_role.get(p["role"], 0) + 1
        if p["joined_on"] and p["joined_on"] >= window_start.isoformat():
            joiners.append(p)

    return {
        "generated_on": today.isoformat(),
        "period": period,
        "total": len(people),
        "active": sum(1 for p in people if p["active"]),
        "by_department": by_dept,
        "by_role": by_role,
        "new_joiners": joiners,
        "attrition_flagged": [p["email"] for p in people if not p["active"]],
    }
