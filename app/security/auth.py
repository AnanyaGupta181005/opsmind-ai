"""Firebase bearer verification with an explicit dev bypass.

The bypass is loud: /health reports auth_mode so nobody ships it by accident.
"""
from __future__ import annotations

import json

from fastapi import Header, HTTPException

from app.config import settings

_fb_app = None


def _firebase():
    global _fb_app
    if _fb_app is None and settings.has_firebase:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(json.loads(settings.firebase_credentials_json))
        _fb_app = firebase_admin.initialize_app(cred)
    return _fb_app


def auth_mode() -> str:
    if settings.has_firebase:
        return "firebase"
    return "dev-bypass" if settings.auth_dev_bypass else "locked"


async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if settings.has_firebase:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(401, "missing bearer token")
        from firebase_admin import auth as fb_auth

        _firebase()
        try:
            decoded = fb_auth.verify_id_token(authorization.split(" ", 1)[1])
        except Exception as exc:
            raise HTTPException(401, f"invalid token: {exc}") from exc
        return {
            "uid": decoded.get("uid"),
            "email": decoded.get("email"),
            "role": decoded.get("role", "admin"),
        }

    if settings.auth_dev_bypass:
        return {"uid": "dev", "email": "dev@local", "role": "admin"}

    raise HTTPException(503, "auth not configured")


async def require_admin(user: dict) -> dict:
    if user.get("role") not in {"admin", "manager"}:
        raise HTTPException(403, "admin or manager role required")
    return user
