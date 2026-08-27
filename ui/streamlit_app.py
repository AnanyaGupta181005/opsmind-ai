"""OpsMind AI - admin console home."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st

import theme
from api_client import ApiError, get, health

theme.apply("Overview")

st.title("OpsMind AI")
st.caption("Natural-language operations orchestrator - admin console")
theme.capability_bar(health())
st.divider()

try:
    hc_dept = get("/employees/stats/headcount", dimension="department")
    hc_role = get("/employees/stats/headcount", dimension="role")
    docs = get("/documents")
    rag = get("/rag/stats")
    tasks = get("/tasks")
except ApiError as exc:
    st.error(str(exc))
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Headcount", hc_dept["total"])
c2.metric("Departments", len(hc_dept["buckets"]))
c3.metric("Indexed chunks", rag.get("chunks", 0))
c4.metric("Background jobs", len(tasks))

st.divider()
left, right = st.columns([3, 2], gap="large")

with left:
    theme.kicker("headcount by department")
    st.bar_chart(hc_dept["buckets"], color=theme.MINT, height=250)
    theme.kicker("headcount by role")
    st.bar_chart(hc_role["buckets"], color=theme.BLUE, height=210)

with right:
    theme.kicker("knowledge base")
    if not docs:
        theme.card(
            "No documents indexed yet. Run <code>python -m scripts.seed</code> to load the "
            "sample handbook, or upload one on the <b>Documents</b> page."
        )
    for d in docs[:6]:
        theme.card(
            "<b>" + d["title"] + "</b><br /><span class='om-kicker'>" + d["kind"] + " - "
            + str(d["chunks"]) + " chunks - "
            + ("indexed" if d["indexed"] else "not indexed") + "</span>"
        )

    theme.kicker("try this in the chat console")
    for q in (
        "Find all interns who joined last month",
        "How much leave does an intern accrue?",
        "Headcount broken down by department",
    ):
        theme.card(q)
