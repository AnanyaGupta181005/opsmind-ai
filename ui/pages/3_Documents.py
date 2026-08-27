"""Document intake: upload, index for RAG, structured extraction."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

import theme
from api_client import ApiError, delete, get, post

theme.apply("Documents")
st.title("Documents")
st.caption("Uploads become retrievable policy chunks; invoices and resumes become structured fields.")

tab_index, tab_extract, tab_library = st.tabs(["Index for RAG", "Extract fields", "Library"])

with tab_index:
    up = st.file_uploader("Handbook, SOP or any policy document",
                          type=["pdf", "txt", "md", "csv"], key="idx")
    kind = st.selectbox("Kind", ["policy", "sop", "other"])
    if up and st.button("Upload and index"):
        try:
            res = post("/documents/upload",
                       files={"file": (up.name, up.getvalue())},
                       data={"kind": kind, "index_for_rag": "true"})
            st.success(res["title"] + " - " + str(res["chunks"]) + " chunks indexed")
        except ApiError as exc:
            st.error(str(exc))
    theme.kicker("how indexing works")
    theme.card(
        "Text is split paragraph-first at ~900 characters with 150 characters of overlap, "
        "embedded with Gemini text-embedding-004, and written to the Supabase "
        "<code>policy_chunks</code> table with a cosine ivfflat index. Without credentials the "
        "same pipeline runs against a deterministic local embedder so retrieval still works."
    )

with tab_extract:
    doc = st.file_uploader("Invoice or resume", type=["pdf", "png", "jpg", "jpeg", "txt"], key="ext")
    ekind = st.radio("Document type", ["invoice", "resume"], horizontal=True)
    if doc and st.button("Extract"):
        try:
            res = post("/documents/extract",
                       files={"file": (doc.name, doc.getvalue())},
                       data={"kind": ekind})
            st.json(res["fields"])
        except ApiError as exc:
            st.error(str(exc))
    theme.card(
        "Gemini Vision parses the page into a fixed JSON schema. Without an API key a regex "
        "heuristic fills what it can, so the screen never dead-ends in a demo."
    )

with tab_library:
    try:
        docs = get("/documents")
        stats = get("/rag/stats")
    except ApiError as exc:
        st.error(str(exc))
        st.stop()
    c1, c2, c3 = st.columns(3)
    c1.metric("Documents", len(docs))
    c2.metric("Chunks", stats.get("chunks", 0))
    c3.metric("Store", stats.get("mode", "?"))
    if docs:
        st.dataframe(
            pd.DataFrame(docs)[["title", "kind", "pages", "chunks", "indexed", "uploaded_at"]],
            use_container_width=True, hide_index=True,
        )
        gone = st.selectbox("Remove document", [d["title"] for d in docs])
        if st.button("Delete and de-index"):
            doc_id = next(d["id"] for d in docs if d["title"] == gone)
            delete("/documents/" + doc_id)
            st.rerun()
    else:
        theme.card("Nothing indexed. Run <code>python -m scripts.seed</code> for a sample handbook.")
