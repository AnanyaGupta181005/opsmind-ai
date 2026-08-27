"""Audit trail: who or what changed the org, and when."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

import theme
from api_client import ApiError, get

theme.apply("Audit Log")
st.title("Audit log")
st.caption("Every write - by an admin or by the agent - lands here.")

try:
    entries = get("/audit", limit=300)
except ApiError as exc:
    st.error(str(exc))
    st.stop()

if not entries:
    theme.card(
        "No writes yet. Onboard someone on the <b>People</b> page, or ask the agent to do it "
        "with write tools armed, and the entry appears here."
    )
    st.stop()

c1, c2 = st.columns(2)
c1.metric("Entries", len(entries))
c2.metric("By agent", sum(1 for e in entries if e.get("actor") == "agent"))

actor = st.selectbox("Actor", ["any"] + sorted({e.get("actor", "?") for e in entries}))
rows = entries if actor == "any" else [e for e in entries if e.get("actor") == actor]

st.dataframe(
    pd.DataFrame(rows)[["at", "actor", "action", "payload"]],
    use_container_width=True, hide_index=True,
)
