from fastapi import APIRouter, Depends

from app.db.mongo import db
from app.security.auth import current_user

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def audit_log(limit: int = 200, user: dict = Depends(current_user)):
    rows = await db.col("audit").find({}, limit=limit)
    rows.sort(key=lambda r: str(r.get("at")), reverse=True)
    return [
        {"at": r.get("at"), "actor": r.get("actor"), "action": r.get("action"),
         "payload": r.get("payload", {})}
        for r in rows
    ]
