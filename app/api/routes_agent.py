from fastapi import APIRouter, Depends

from app.agent.gemini_agent import run
from app.db.mongo import db
from app.models.schemas import ChatRequest, ChatResponse
from app.security.auth import current_user

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, user: dict = Depends(current_user)):
    return await run(body.session_id, body.message, allow_writes=body.allow_writes)


@router.get("/history/{session_id}")
async def history(session_id: str, user: dict = Depends(current_user)):
    turns = await db.col("chat_turns").find({"session_id": session_id}, limit=200)
    return [
        {"role": t.get("role"), "content": t.get("content"),
         "tool_calls": t.get("tool_calls", []), "citations": t.get("citations", []),
         "created_at": t.get("created_at")}
        for t in turns
    ]


@router.get("/tools")
async def list_tools(allow_writes: bool = True, user: dict = Depends(current_user)):
    from app.agent.tools import declarations_for

    return {"tools": declarations_for(allow_writes)}
