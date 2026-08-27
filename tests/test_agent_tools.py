import pytest

from app.agent import tools
from app.agent.gemini_agent import run

pytestmark = pytest.mark.asyncio


async def test_search_employees_filters_by_role():
    res = await tools.search_employees(role="intern")
    assert res["count"] >= 1
    assert all(e["role"] == "intern" for e in res["employees"])


async def test_headcount_buckets_sum_to_total():
    res = await tools.headcount_by("department")
    assert sum(res["buckets"].values()) == res["total"]


async def test_create_employee_rejects_duplicate_email():
    first = await tools.create_employee("Test One", "dup@inbenne.com")
    assert first["ok"]
    second = await tools.create_employee("Test Two", "dup@inbenne.com")
    assert not second["ok"]


async def test_read_only_session_hides_write_tools():
    names = {d["name"] for d in tools.declarations_for(allow_writes=False)}
    assert "create_employee" not in names
    assert "search_employees" in names


async def test_agent_routes_policy_question_through_rag():
    out = await run("t1", "what is the leave policy for interns", allow_writes=False)
    assert any(c["name"] == "search_policy" for c in out["tool_calls"])
