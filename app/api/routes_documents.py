import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.db.mongo import db
from app.models.schemas import DocumentMeta
from app.rag.chunking import chunk_text
from app.rag.store import store
from app.security.auth import current_user
from app.services.ocr import extract_text, structured_extract

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentMeta])
async def list_documents(kind: str | None = None, user: dict = Depends(current_user)):
    flt = {"kind": kind} if kind else {}
    docs = await db.col("documents").find(flt, limit=200)
    return [
        {
            "id": str(d["_id"]), "title": d["title"], "kind": d.get("kind", "other"),
            "pages": d.get("pages", 1), "chunks": d.get("chunks", 0),
            "uploaded_at": d.get("uploaded_at"), "indexed": d.get("indexed", False),
            "source": d.get("source", "upload"),
        }
        for d in docs
    ]


@router.post("/upload", response_model=DocumentMeta, status_code=201)
async def upload(
    file: UploadFile = File(...),
    kind: str = Form("policy"),
    index_for_rag: bool = Form(True),
    user: dict = Depends(current_user),
):
    data = await file.read()
    if not data:
        raise HTTPException(400, "empty file")

    text, pages = extract_text(file.filename or "upload", data)
    doc_id = str(uuid.uuid4())
    n_chunks = 0

    if index_for_rag and text.strip():
        n_chunks = store.upsert(doc_id, file.filename or "untitled", kind, chunk_text(text))

    meta = {
        "_id": doc_id, "title": file.filename or "untitled", "kind": kind,
        "pages": pages, "chunks": n_chunks,
        "uploaded_at": datetime.now(timezone.utc),
        "indexed": n_chunks > 0, "source": "upload",
        "text_preview": text[:2000],
    }
    await db.col("documents").insert_one(meta)
    await db.audit(user["email"], "document.upload", {"doc_id": doc_id, "kind": kind})
    return {**meta, "id": doc_id}


@router.post("/extract")
async def extract(
    file: UploadFile = File(...),
    kind: str = Form("invoice"),
    user: dict = Depends(current_user),
):
    """Gemini Vision / heuristic structured extraction for invoices and resumes."""
    if kind not in {"invoice", "resume"}:
        raise HTTPException(400, "kind must be invoice or resume")
    data = await file.read()
    text, _ = extract_text(file.filename or "upload", data)
    is_image = (file.filename or "").lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    fields = structured_extract(kind, text, image=data if is_image else None)
    return {"kind": kind, "filename": file.filename, "fields": fields}


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(current_user)):
    n = await db.col("documents").delete_one({"_id": doc_id})
    store.delete_doc(doc_id)
    if not n:
        raise HTTPException(404, "document not found")
    return {"ok": True, "doc_id": doc_id}
