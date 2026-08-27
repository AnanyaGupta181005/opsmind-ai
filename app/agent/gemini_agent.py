"""Manager Agent: Gemini function-calling loop with a deterministic fallback.

Design notes
------------
* Bounded loop (MAX_STEPS) so a confused model cannot spin.
* Every tool invocation is recorded as a ToolCall for the UI trace.
* Policy questions are forced through RAG by the system instruction, and the
  resulting citations are surfaced to the caller rather than buried in prose.
* Without GEMINI_API_KEY the agent runs a rule-based planner over the same
  tools, so the product is demoable and the tools stay under test.
"""
from __future__ import annotations

import json
import re
import time
from datetime import date, timedelta

from app.agent.tools import REGISTRY, declarations_for, utc_now
from app.config import settings
from app.db.mongo import db

MAX_STEPS = 6

SYSTEM = """You are OpsMind, the operations manager agent for a company.

Rules:
- You EXECUTE work using tools. Prefer a tool over guessing.
- Any question about policy, handbook, leave, reimbursement or process MUST go
  through search_policy. Never answer policy from your own knowledge.
- People questions go through search_employees or headcount_by.
- Convert relative dates ("last month", "this quarter") into ISO dates before
  calling tools. Today is {today}.
- Be terse and operational. Report numbers, names and next actions. No filler.
- If a write tool is unavailable, say the session is read-only and stop.
"""


async def _run_tool(name: str, args: dict) -> tuple[dict, int, bool]:
    t0 = time.perf_counter()
    fn = REGISTRY.get(name)
    if fn is None:
        return {"error": f"unknown tool {name}"}, 0, False
    try:
        result = await fn(**args)
        ok = True
    except Exception as exc:
        result, ok = {"error": str(exc)}, False
    return result, int((time.perf_counter() - t0) * 1000), ok


def _summarise(name: str, result: dict) -> str:
    if "error" in result:
        return f"failed: {result['error']}"
    if name == "search_employees":
        return f"{result.get('count', 0)} match(es)"
    if name == "headcount_by":
        return f"{result.get('total', 0)} people across {len(result.get('buckets', {}))} buckets"
    if name == "search_policy":
        return f"{len(result.get('citations', []))} passage(s), grounded={result.get('grounded')}"
    if name == "list_documents":
        return f"{result.get('count', 0)} document(s)"
    return "ok"


# --------------------------------------------------------------------- live
async def _run_gemini(message: str, history: list[dict], allow_writes: bool) -> dict:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        settings.gemini_model,
        tools=[{"function_declarations": declarations_for(allow_writes)}],
        system_instruction=SYSTEM.format(today=date.today().isoformat()),
    )
    chat = model.start_chat(history=history)

    calls: list[dict] = []
    citations: list[dict] = []
    reply = ""
    payload = message

    for _ in range(MAX_STEPS):
        resp = chat.send_message(payload)
        parts = resp.candidates[0].content.parts
        fcalls = [p.function_call for p in parts if getattr(p, "function_call", None)]

        if not fcalls:
            reply = "".join(getattr(p, "text", "") for p in parts).strip()
            break

        responses = []
        for fc in fcalls:
            args = dict(fc.args or {})
            result, ms, ok = await _run_tool(fc.name, args)
            calls.append(
                {
                    "name": fc.name,
                    "args": args,
                    "result_summary": _summarise(fc.name, result),
                    "ok": ok,
                    "duration_ms": ms,
                }
            )
            if fc.name == "search_policy":
                citations.extend(result.get("citations", []))
            responses.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fc.name, response={"result": json.dumps(result, default=str)[:12000]}
                    )
                )
            )
        payload = responses

    return {"reply": reply or "(no response)", "tool_calls": calls, "citations": citations}


# --------------------------------------------------------------------- mock
_LAST_MONTH = re.compile(r"last month", re.I)
_INTERN = re.compile(r"intern", re.I)
_POLICY = re.compile(r"policy|handbook|leave|reimburse|holiday|wfh|notice period|sop", re.I)
_COUNT = re.compile(r"how many|headcount|count|breakdown", re.I)


async def _run_rules(message: str, allow_writes: bool) -> dict:
    calls: list[dict] = []
    citations: list[dict] = []

    async def call(name: str, **args):
        result, ms, ok = await _run_tool(name, args)
        calls.append(
            {"name": name, "args": args, "result_summary": _summarise(name, result),
             "ok": ok, "duration_ms": ms}
        )
        return result

    if _POLICY.search(message):
        res = await call("search_policy", question=message)
        citations = res.get("citations", [])
        return {"reply": res.get("answer", ""), "tool_calls": calls, "citations": citations}

    if _COUNT.search(message):
        dim = "role" if re.search(r"role|intern|engineer|manager", message, re.I) else "department"
        res = await call("headcount_by", dimension=dim)
        rows = ", ".join(f"{k}: {v}" for k, v in sorted(res["buckets"].items()))
        return {"reply": f"Headcount by {dim} — {rows}. Total {res['total']}.",
                "tool_calls": calls, "citations": []}

    args: dict = {"limit": 25}
    if _INTERN.search(message):
        args["role"] = "intern"
    if _LAST_MONTH.search(message):
        today = date.today()
        first_this = today.replace(day=1)
        last_prev = first_this - timedelta(days=1)
        args["joined_after"] = last_prev.replace(day=1).isoformat()
        args["joined_before"] = last_prev.isoformat()
    res = await call("search_employees", **args)
    if res["count"] == 0:
        reply = "No employees matched that filter."
    else:
        names = "; ".join(f"{e['name']} ({e['role']}, {e['department']}, joined {e['joined_on']})"
                          for e in res["employees"][:10])
        reply = f"{res['count']} match(es): {names}"
    return {"reply": reply, "tool_calls": calls, "citations": citations}


# ---------------------------------------------------------------- entrypoint
async def run(session_id: str, message: str, allow_writes: bool = False) -> dict:
    t0 = time.perf_counter()
    turns = await db.col("chat_turns").find({"session_id": session_id}, limit=20)

    if settings.has_gemini:
        history = [
            {"role": "user" if t["role"] == "user" else "model",
             "parts": [t.get("content", "")]}
            for t in turns
        ]
        try:
            out = await _run_gemini(message, history, allow_writes)
            mode = "live"
        except Exception as exc:
            out = await _run_rules(message, allow_writes)
            out["reply"] += f"\n\n(fell back to rule planner: {exc})"
            mode = "mock"
    else:
        out = await _run_rules(message, allow_writes)
        mode = "mock"

    now = utc_now()
    await db.col("chat_turns").insert_one(
        {"session_id": session_id, "role": "user", "content": message, "created_at": now}
    )
    await db.col("chat_turns").insert_one(
        {"session_id": session_id, "role": "agent", "content": out["reply"],
         "tool_calls": out["tool_calls"], "citations": out["citations"], "created_at": now}
    )

    return {
        "session_id": session_id,
        "reply": out["reply"],
        "tool_calls": out["tool_calls"],
        "citations": out["citations"],
        "latency_ms": int((time.perf_counter() - t0) * 1000),
        "mode": mode,
    }
