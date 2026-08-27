"""Paragraph-aware chunking. Keeps policy clauses whole where possible."""
from __future__ import annotations

import re

from app.config import settings

_SPLIT = re.compile(r"\n\s*\n")


def chunk_text(text: str, size: int | None = None, overlap: int | None = None) -> list[str]:
    size = size or settings.rag_chunk_size
    overlap = overlap or settings.rag_chunk_overlap
    paras = [p.strip() for p in _SPLIT.split(text or "") if p.strip()]

    chunks: list[str] = []
    buf = ""
    for para in paras:
        if len(buf) + len(para) + 2 <= size:
            buf = f"{buf}\n\n{para}".strip()
            continue
        if buf:
            chunks.append(buf)
        if len(para) <= size:
            buf = para
        else:  # a single oversized paragraph: hard-window it
            for i in range(0, len(para), size - overlap):
                piece = para[i : i + size]
                if piece.strip():
                    chunks.append(piece.strip())
            buf = ""
    if buf:
        chunks.append(buf)

    # re-introduce a tail overlap so clause boundaries are never lost
    if overlap and len(chunks) > 1:
        stitched = [chunks[0]]
        for prev, cur in zip(chunks, chunks[1:]):
            stitched.append((prev[-overlap:] + "\n" + cur).strip())
        return stitched
    return chunks
