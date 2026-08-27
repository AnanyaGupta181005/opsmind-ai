from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.models.schemas import RagAnswer
from app.rag.chunking import chunk_text
from app.rag.pipeline import answer
from app.rag.store import store
from app.security.auth import current_user

router = APIRouter(prefix="/rag", tags=["rag"])


class AskBody(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int | None = None
    kind: str | None = None


class IndexBody(BaseModel):
    title: str
    kind: str = "policy"
    content: str = Field(min_length=20)


@router.post("/ask", response_model=RagAnswer)
async def ask(body: AskBody, user: dict = Depends(current_user)):
    return answer(body.question, top_k=body.top_k, kind=body.kind)


@router.post("/search")
async def search(body: AskBody, user: dict = Depends(current_user)):
    """Raw retrieval, no generation — useful for tuning top_k and thresholds."""
    return {"hits": store.search(body.question, top_k=body.top_k, kind=body.kind)}


@router.post("/index")
async def index_text(body: IndexBody, user: dict = Depends(current_user)):
    import uuid

    doc_id = str(uuid.uuid4())
    n = store.upsert(doc_id, body.title, body.kind, chunk_text(body.content))
    return {"ok": True, "doc_id": doc_id, "chunks": n, "index": store.stats()}


@router.get("/stats")
async def stats(user: dict = Depends(current_user)):
    return store.stats()
