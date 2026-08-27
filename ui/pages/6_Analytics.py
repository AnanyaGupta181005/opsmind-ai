"""Org analytics computed from the same report service the workers use."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

import theme
from api_client import ApiError, get

theme.apply("Analytics")
st.title("Analytics")
st.caption("One report service, shared by this page, the API and the Celery worker.")

period = st.radio("Window", ["month", "quarter"], horizontal=True)
try:
    rep = get("/tasks/report/preview", period=period)
except ApiError as exc:
    st.error(str(exc))
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", rep["total"])
c2.metric("Active", rep["active"])
c3.metric("New joiners", len(rep["new_joiners"]))
c4.metric("Inactive", len(rep["attrition_flagged"]))

left, right = st.columns(2, gap="large")
with left:
    theme.kicker("by department")
    st.bar_chart(rep["by_department"], color=theme.MINT, height=280)
with right:
    theme.kicker("by role")
    st.bar_chart(rep["by_role"], color=theme.BLUE, height=280)

st.divider()
theme.kicker("new joiners in window")
if rep["new_joiners"]:
    st.dataframe(
        pd.DataFrame(rep["new_joiners"])[["name", "role", "department", "joined_on"]],
        use_container_width=True, hide_index=True,
    )
else:
    theme.card("No one joined in this window.")

with st.expander("Raw report payload"):
    st.json(rep)
