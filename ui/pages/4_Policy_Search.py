"""RAG surface: grounded answers plus the raw retrieval view for tuning."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

import theme
from api_client import ApiError, get, post

theme.apply("Policy Search")
st.title("Policy search")
st.caption("Retrieval-augmented answers over the indexed handbook set, with the evidence shown.")

try:
    stats = get("/rag/stats")
except ApiError as exc:
    st.error(str(exc))
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Store", stats.get("mode", "?"))
c2.metric("Documents", stats.get("docs", 0))
c3.metric("Chunks", stats.get("chunks", 0))

with st.sidebar:
    st.markdown("### Retrieval")
    top_k = st.slider("top_k", 1, 12, 5)
    kind = st.selectbox("Restrict to kind", ["any", "policy", "sop", "invoice", "resume", "other"])
    show_raw = st.toggle("Show raw retrieval", value=True)

q = st.text_input("Question", placeholder="Can an intern carry unused leave into next year?")
if st.button("Ask") and q:
    body = {"question": q, "top_k": top_k, "kind": None if kind == "any" else kind}
    try:
        res = post("/rag/ask", json=body)
    except ApiError as exc:
        st.error(str(exc))
        st.stop()

    if not res["grounded"]:
        st.warning("Not grounded - the indexed set does not cover this.")
    st.markdown("### Answer")
    st.markdown(res["answer"])
    st.caption(str(res["latency_ms"]) + " ms - " + str(len(res["citations"])) + " citation(s)")
    theme.render_citations(res["citations"])

    if show_raw:
        st.divider()
        theme.kicker("raw retrieval - score before threshold")
        hits = post("/rag/search", json=body)["hits"]
        if hits:
            st.dataframe(
                pd.DataFrame(hits)[["title", "chunk_index", "score", "content"]],
                use_container_width=True, hide_index=True,
            )

st.divider()
theme.kicker("index text directly")
with st.form("index_text"):
    title = st.text_input("Title", "Ad-hoc policy note")
    ikind = st.selectbox("Kind", ["policy", "sop", "other"], key="ik")
    content = st.text_area("Content", height=160)
    if st.form_submit_button("Index") and len(content) > 20:
        res = post("/rag/index", json={"title": title, "kind": ikind, "content": content})
        st.success(str(res["chunks"]) + " chunks indexed")
