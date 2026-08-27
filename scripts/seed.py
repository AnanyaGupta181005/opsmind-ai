"""Seed the vector store with a sample handbook so RAG works on first boot.

    python -m scripts.seed
"""
import asyncio
import uuid
from datetime import datetime, timezone

from app.db.mongo import db
from app.rag.chunking import chunk_text
from app.rag.store import store

HANDBOOK = """
Leave Policy

Every full-time employee accrues 18 days of paid leave per calendar year, accruing
at 1.5 days per completed month. Unused leave carries over up to a maximum of 9
days into the next year; anything beyond that lapses on 31 March.

Interns accrue 1 day of paid leave per completed month of the internship and may
not carry leave over. Leave requests must be raised at least 3 working days in
advance through the OpsMind portal and are approved by the reporting manager.

Sick Leave

Sick leave is 8 days per year and does not require advance notice. Absences longer
than 3 consecutive days require a medical certificate submitted to People Ops
within 7 days of returning.

Work From Home

Employees may work remotely up to 8 days per month with manager approval. Teams on
on-call rotation must be in office on their rotation days. Fully remote arrangements
require a written exception approved by the department head and People Ops.

Reimbursement Policy

Business expenses are reimbursed within 15 working days of claim submission. Claims
must include an itemised invoice and be submitted within 30 days of the expense.
Meal claims are capped at INR 800 per day of approved travel; intercity travel is
reimbursed at actuals in sleeper or economy class. Any single expense above
INR 25,000 requires prior written approval from the department head.

Notice Period

Engineers and designers serve 60 days of notice. Managers and above serve 90 days.
Interns serve 15 days. Notice may be shortened only by mutual written agreement,
and unserved notice is recovered from the final settlement.

Data and Security

Company data must not be copied to personal devices or personal cloud accounts.
Production database access requires a ticket, a stated purpose and expires after
24 hours. Sharing credentials is grounds for immediate termination.
"""

SOP = """
New Joiner Onboarding SOP

Day minus 3: People Ops creates the employee record in OpsMind, assigns a reporting
manager and triggers the hardware request workflow.

Day 0: IT issues the laptop and provisions email, VPN and repository access with
least-privilege defaults. The joiner signs the data-handling acknowledgement.

Day 1 to 5: The reporting manager assigns a starter task and a buddy. The joiner
completes security training. People Ops verifies documents and payroll details.

Day 30: Manager files a first-month check-in note against the employee record.
Access review runs automatically and revokes anything unused for 21 days.
"""


async def main() -> None:
    for title, kind, body in (
        ("Employee Handbook 2026.pdf", "policy", HANDBOOK),
        ("Onboarding SOP.md", "sop", SOP),
    ):
        doc_id = str(uuid.uuid4())
        n = store.upsert(doc_id, title, kind, chunk_text(body))
        await db.col("documents").insert_one(
            {"_id": doc_id, "title": title, "kind": kind, "pages": 1, "chunks": n,
             "uploaded_at": datetime.now(timezone.utc), "indexed": True, "source": "seed"}
        )
        print(f"indexed {title}: {n} chunks")
    print("vector store:", store.stats())


if __name__ == "__main__":
    asyncio.run(main())
