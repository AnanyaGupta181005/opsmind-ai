"""Embeddings with a deterministic offline fallback.

Live: Gemini text-embedding-004 (768-d).
Mock: hashed bag-of-trigrams projected to 768-d, L2-normalised. Not semantic,
but stable and good enough that retrieval demos work with zero credentials.
"""
from __future__ import annotations

import hashlib
import math

from app.config import settings

DIM = 768


def _hash_embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    t = f"  {text.lower()}  "
    for i in range(len(t) - 2):
        gram = t[i : i + 3]
        h = int(hashlib.blake2b(gram.encode(), digest_size=8).hexdigest(), 16)
        vec[h % DIM] += 1.0
        vec[(h >> 17) % DIM] -= 0.5
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def embed(texts: list[str], task: str = "retrieval_document") -> list[list[float]]:
    if not settings.has_gemini:
        return [_hash_embed(t) for t in texts]
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    out: list[list[float]] = []
    for t in texts:
        try:
            res = genai.embed_content(
                model=f"models/{settings.gemini_embed_model}",
                content=t,
                task_type=task,
            )
            out.append(list(res["embedding"]))
        except Exception:
            out.append(_hash_embed(t))
    return out


def embed_one(text: str, task: str = "retrieval_query") -> list[float]:
    return embed([text], task=task)[0]


def cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a)) or 1.0
    db_ = math.sqrt(sum(y * y for y in b)) or 1.0
    return num / (da * db_)
