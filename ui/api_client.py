"""Thin API client shared by every Streamlit page."""
from __future__ import annotations

import os

import requests

BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
TIMEOUT = 60


class ApiError(RuntimeError):
    pass


def _req(method: str, path: str, **kw):
    try:
        r = requests.request(method, f"{BASE}{path}", timeout=TIMEOUT, **kw)
    except requests.RequestException as exc:
        raise ApiError(f"cannot reach API at {BASE} - {exc}") from exc
    if r.status_code >= 400:
        raise ApiError(f"{r.status_code}: {r.text[:300]}")
    return r.json() if r.content else {}


def get(path, **params):
    return _req("GET", path, params=params or None)


def post(path, json=None, files=None, data=None):
    return _req("POST", path, json=json, files=files, data=data)


def delete(path):
    return _req("DELETE", path)


def health():
    try:
        return get("/health")
    except ApiError:
        return None
