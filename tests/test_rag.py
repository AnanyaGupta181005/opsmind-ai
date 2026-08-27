import pytest

from app.rag.chunking import chunk_text
from app.rag.pipeline import answer
from app.rag.store import VectorStore

HANDBOOK = """Leave Policy

Full-time employees accrue 18 days of paid leave per year.

Reimbursement Policy

Claims are reimbursed within 15 working days and meals are capped at INR 800 per day.
"""


def test_chunking_keeps_paragraphs():
    chunks = chunk_text(HANDBOOK, size=200, overlap=20)
    assert chunks
    assert any("Leave Policy" in c for c in chunks)


def test_retrieval_ranks_relevant_chunk_first():
    s = VectorStore()
    s.upsert("doc-1", "Handbook", "policy", chunk_text(HANDBOOK, size=200, overlap=20))
    hits = s.search("reimbursement meal cap", top_k=3)
    assert hits
    assert "reimburse" in hits[0]["content"].lower()


def test_answer_refuses_when_nothing_indexed(monkeypatch):
    from app.rag import pipeline

    monkeypatch.setattr(pipeline.store, "search", lambda *a, **k: [])
    out = answer("what is the parking policy")
    assert out["grounded"] is False
    assert not out["citations"]
