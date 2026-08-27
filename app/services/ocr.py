"""Document understanding: text extraction + Gemini Vision structured parse."""
from __future__ import annotations

import io
import json
import re

from app.config import settings


def extract_text(filename: str, data: bytes) -> tuple[str, int]:
    """Returns (text, pages). Handles pdf, txt/md; images defer to vision."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            pages = [p.extract_text() or "" for p in reader.pages]
            return "\n\n".join(pages), len(pages)
        except Exception:
            return "", 0
    if lower.endswith((".txt", ".md", ".csv")):
        return data.decode("utf-8", errors="ignore"), 1
    return "", 1


_JSON = re.compile(r"\{.*\}", re.S)


def _parse_json(text: str) -> dict:
    m = _JSON.search(text or "")
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}


def structured_extract(kind: str, text: str, image: bytes | None = None) -> dict:
    """kind: invoice | resume. Gemini when available, regex heuristics otherwise."""
    if settings.has_gemini:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        schema = {
            "invoice": '{"vendor":str,"invoice_number":str,"issued_on":"YYYY-MM-DD",'
                       '"total":number,"currency":str,"line_items":[{"desc":str,"amount":number}]}',
            "resume": '{"name":str,"email":str,"years_experience":number,'
                      '"skills":[str],"education":[str]}',
        }[kind]
        parts = [f"Extract this JSON exactly, nulls where unknown: {schema}\n\n{text[:12000]}"]
        if image:
            parts.append({"mime_type": "image/png", "data": image})
        try:
            return _parse_json(model.generate_content(parts).text)
        except Exception:
            pass

    # heuristic fallback
    if kind == "invoice":
        total = re.search(r"(?:total|amount due)[^0-9]{0,12}([0-9][0-9,.]*)", text, re.I)
        num = re.search(r"invoice\s*(?:no\.?|#|number)?\s*[:\-]?\s*([A-Z0-9\-/]{3,})", text, re.I)
        return {
            "vendor": (text.strip().splitlines() or [""])[0][:80] or None,
            "invoice_number": num.group(1) if num else None,
            "total": float(total.group(1).replace(",", "")) if total else None,
            "currency": "INR",
            "line_items": [],
        }
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    skills = [s for s in ("python", "fastapi", "mongodb", "docker", "react", "sql", "gemini")
              if re.search(s, text, re.I)]
    return {
        "name": (text.strip().splitlines() or [""])[0][:80] or None,
        "email": email.group(0) if email else None,
        "years_experience": None,
        "skills": skills,
        "education": [],
    }
