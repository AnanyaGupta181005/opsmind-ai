"""Celery app. Import-safe when Redis is absent (tasks then run inline)."""
from __future__ import annotations

from app.config import settings

celery_app = None
try:
    from celery import Celery

    celery_app = Celery("opsmind", broker=settings.redis_url, backend=settings.redis_url)
    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        task_time_limit=600,
        timezone="UTC",
    )
except Exception:  # celery missing or misconfigured
    celery_app = None


def broker_available() -> bool:
    if celery_app is None:
        return False
    try:
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=0, timeout=1)
        conn.release()
        return True
    except Exception:
        return False
