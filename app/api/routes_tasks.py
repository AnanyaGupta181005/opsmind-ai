import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.security.auth import current_user
from app.services.reports import headcount_report
from app.workers.tasks import list_tasks, submit_report

router = APIRouter(prefix="/tasks", tags=["tasks"])


class ReportBody(BaseModel):
    report: str = "headcount"
    period: str = "month"


@router.get("")
async def all_tasks(limit: int = 50, user: dict = Depends(current_user)):
    return await list_tasks(limit)


@router.post("/report")
async def queue_report(body: ReportBody, user: dict = Depends(current_user)):
    return await submit_report(body.report, body.period)


@router.get("/report/preview")
async def preview_report(period: str = "month", user: dict = Depends(current_user)):
    return await headcount_report(period)


class WebBody(BaseModel):
    url: str
    timeout_ms: int = 15000


@router.post("/web")
async def browser_task(body: WebBody, user: dict = Depends(current_user)):
    """Playwright fetch. Reports installation problems instead of hiding them."""
    from app.services.web_tasks import fetch_page

    return await fetch_page(body.url, body.timeout_ms)


class WebhookBody(BaseModel):
    event: str
    payload: dict = {}


@router.post("/n8n")
async def trigger_n8n(body: WebhookBody, user: dict = Depends(current_user)):
    if not settings.n8n_webhook_url:
        raise HTTPException(503, "N8N_WEBHOOK_URL not configured")
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(settings.n8n_webhook_url, json=body.model_dump())
    return {"ok": r.status_code < 400, "status": r.status_code}
