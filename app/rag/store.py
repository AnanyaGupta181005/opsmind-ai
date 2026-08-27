"""Vector store: Supabase pgvector when configured, in-process otherwise."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.config import settings
from app.rag.embeddings import cosine, embed


@dataclass
class StoredChunk:
    id: str
    doc_id: str
    title: str
    kind: str
    chunk_index: int
    content: str
    embedding: list[float] = field(default_factory=list)


class VectorStore:
    def __init__(self) -> None:
        self.mode = "supabase" if settings.has_supabase else "memory"
        self._mem: list[StoredChunk] = []
        self._client = None
        if self.mode == "supabase":
            from supabase import create_client

            self._client = create_client(settings.supabase_url, settings.supabase_service_key)

    # ---------------------------------------------------------------- write
    def upsert(self, doc_id: str, title: str, kind: str, chunks: list[str]) -> int:
        vectors = embed(chunks, task="retrieval_document")
        rows = [
            {
                "id": str(uuid.uuid4()),
                "doc_id": doc_id,
                "title": title,
                "kind": kind,
                "chunk_index": i,
                "content": c,
                "embedding": v,
            }
            for i, (c, v) in enumerate(zip(chunks, vectors))
        ]
        if self.mode == "supabase":
            self._client.table(settings.supabase_docs_table).insert(rows).execute()
        else:
            self._mem.extend(StoredChunk(**r) for r in rows)
        return len(rows)

    def delete_doc(self, doc_id: str) -> None:
        if self.mode == "supabase":
            self._client.table(settings.supabase_docs_table).delete().eq("doc_id", doc_id).execute()
        else:
            self._mem = [c for c in self._mem if c.doc_id != doc_id]

    # ----------------------------------------------------------------- read
    def search(self, query: str, top_k: int | None = None, kind: str | None = None) -> list[dict]:
        top_k = top_k or settings.rag_top_k
        qvec = embed([query], task="retrieval_query")[0]

        if self.mode == "supabase":
            res = self._client.rpc(
                "match_policy_chunks",
                {"query_embedding": qvec, "match_count": top_k, "filter_kind": kind},
            ).execute()
            rows = res.data or []
            return [
                {
                    "doc_id": r["doc_id"],
                    "title": r["title"],
                    "chunk_index": r["chunk_index"],
                    "content": r["content"],
                    "score": float(r.get("similarity", 0.0)),
                }
                for r in rows
            ]

        pool = [c for c in self._mem if kind is None or c.kind == kind]
        scored = [
            {
                "doc_id": c.doc_id,
                "title": c.title,
                "chunk_index": c.chunk_index,
                "content": c.content,
                "score": cosine(qvec, c.embedding),
            }
            for c in pool
        ]
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]

    def stats(self) -> dict:
        if self.mode == "supabase":
            res = self._client.table(settings.supabase_docs_table).select("doc_id").execute()
            rows = res.data or []
            return {"mode": self.mode, "chunks": len(rows), "docs": len({r["doc_id"] for r in rows})}
        return {
            "mode": self.mode,
            "chunks": len(self._mem),
            "docs": len({c.doc_id for c in self._mem}),
        }


store = VectorStore()
