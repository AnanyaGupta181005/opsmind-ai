"""Retrieve -> rerank -> generate, with citations and refusal on weak evidence."""
from __future__ import annotations

import time

from app.config import settings
from app.rag.store import store

SYSTEM = (
    "You are OpsMind's policy analyst. Answer ONLY from the numbered context. "
    "Cite the sources you used as [1], [2]. If the context does not contain the "
    "answer, say plainly that the handbook does not cover it and suggest who to ask. "
    "Never invent policy."
)


def _prompt(question: str, hits: list[dict]) -> str:
    ctx = "\n\n".join(
        f"[{i + 1}] ({h['title']} · chunk {h['chunk_index']})\n{h['content']}"
        for i, h in enumerate(hits)
    )
    return f"{SYSTEM}\n\nCONTEXT\n{ctx}\n\nQUESTION\n{question}\n\nANSWER"


def _extractive_answer(question: str, hits: list[dict]) -> str:
    """Offline answer: stitch the strongest passages, clearly labelled."""
    lead = hits[0]["content"].strip()
    if len(lead) > 700:
        lead = lead[:700].rsplit(" ", 1)[0] + "…"
    return (
        f"From the indexed handbook [1]:\n\n{lead}\n\n"
        f"(Offline retrieval mode — {len(hits)} passages matched. "
        "Add GEMINI_API_KEY for a synthesised answer.)"
    )


def answer(question: str, top_k: int | None = None, kind: str | None = None) -> dict:
    t0 = time.perf_counter()
    hits = [
        h for h in store.search(question, top_k=top_k, kind=kind)
        if h["score"] >= settings.rag_min_score
    ]

    if not hits:
        return {
            "question": question,
            "answer": "Nothing in the indexed policy set covers that. Upload the relevant "
                      "handbook under Documents, or route the question to People Ops.",
            "citations": [],
            "grounded": False,
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }

    if settings.has_gemini:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        try:
            text = model.generate_content(_prompt(question, hits)).text
        except Exception as exc:  # network / quota
            text = _extractive_answer(question, hits) + f"\n\n(model error: {exc})"
    else:
        text = _extractive_answer(question, hits)

    return {
        "question": question,
        "answer": text,
        "citations": [
            {
                "doc_id": h["doc_id"],
                "title": h["title"],
                "chunk_index": h["chunk_index"],
                "score": round(h["score"], 4),
                "snippet": h["content"][:280],
            }
            for h in hits
        ],
        "grounded": True,
        "latency_ms": int((time.perf_counter() - t0) * 1000),
    }
