"""Agent chat with a visible tool trace and citations."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st

import theme
from api_client import ApiError, post

theme.apply("Chat Console")
st.title("Chat console")
st.caption("Every reply shows which tools ran and which passages grounded it.")

with st.sidebar:
    st.markdown("### Session")
    session = st.text_input("Session id", value="admin-console")
    allow_writes = st.toggle("Allow write tools", value=False,
                             help="Off = read-only. On = the agent may create or deactivate records.")
    if allow_writes:
        st.warning("Write tools are armed.")
    if st.button("Clear transcript"):
        st.session_state.pop("turns", None)
        st.rerun()

if "turns" not in st.session_state:
    st.session_state.turns = []

for t in st.session_state.turns:
    with st.chat_message("user" if t["role"] == "user" else "assistant"):
        st.markdown(t["content"])
        theme.render_tool_calls(t.get("tool_calls", []))
        theme.render_citations(t.get("citations", []))

prompt = st.chat_input("Ask OpsMind to find, count, explain or do something...")
if prompt:
    st.session_state.turns.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("planning"):
            try:
                res = post("/agent/chat", json={
                    "session_id": session, "message": prompt, "allow_writes": allow_writes,
                })
            except ApiError as exc:
                st.error(str(exc))
                st.stop()
        st.markdown(res["reply"])
        theme.render_tool_calls(res.get("tool_calls", []))
        theme.render_citations(res.get("citations", []))
        st.caption(res["mode"] + " - " + str(res["latency_ms"]) + " ms")
    st.session_state.turns.append({
        "role": "agent", "content": res["reply"],
        "tool_calls": res.get("tool_calls", []), "citations": res.get("citations", []),
    })
