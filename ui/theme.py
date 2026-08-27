"""One place for the console look: Streamlit page config + injected CSS."""
import streamlit as st

BG = "#141618"
SURFACE = "#1d2023"
LINE = "#2e3338"
TEXT = "#f0f1f2"
MUTED = "#9aa1a8"
MINT = "#4fd1a5"
BLUE = "#6ba8f5"
AMBER = "#e0a75a"
ROSE = "#e58a7b"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family:'IBM Plex Sans', system-ui, sans-serif; }
.stApp { background:__BG__; color:__TEXT__; }
section[data-testid="stSidebar"] { background:__SURFACE__; border-right:1px solid __LINE__; }
h1 { font-size:1.6rem !important; font-weight:600 !important; letter-spacing:.005em; }
h2 { font-size:1.15rem !important; font-weight:600 !important; }
code, pre { font-family:'IBM Plex Mono', monospace !important; }
div[data-testid="stMetric"] {
  background:__SURFACE__; border:1px solid __LINE__; border-radius:12px; padding:14px 16px;
}
div[data-testid="stMetricLabel"] p {
  font-family:'IBM Plex Mono',monospace; font-size:.72rem !important;
  text-transform:uppercase; letter-spacing:.07em; color:__MUTED__ !important;
}
.stButton>button {
  background:__MINT__; color:__BG__; border:0; border-radius:9px;
  font-weight:600; padding:.45rem 1.1rem;
}
.stButton>button:hover { background:__BLUE__; color:__BG__; }
div[data-testid="stDataFrame"] { border:1px solid __LINE__; border-radius:12px; }
.om-card {
  background:__SURFACE__; border:1px solid __LINE__; border-radius:12px;
  padding:15px 17px; margin-bottom:11px;
}
.om-tag {
  display:inline-flex; gap:6px; align-items:center; font-family:'IBM Plex Mono',monospace;
  font-size:.7rem; padding:4px 9px; border-radius:999px;
  border:1px solid __LINE__; color:__MUTED__; margin-right:6px;
}
.om-live { color:__MINT__; border-color:__MINT__; }
.om-mock { color:__AMBER__; border-color:__AMBER__; }
.om-kicker {
  font-family:'IBM Plex Mono',monospace; font-size:.7rem; text-transform:uppercase;
  letter-spacing:.09em; color:__MUTED__; margin:2px 0 8px;
}
.om-cite { border-left:2px solid __MINT__; padding:2px 0 2px 12px; margin:10px 0;
  color:__MUTED__; font-size:.88rem; }
.om-cite b { color:__TEXT__; font-weight:500; }
.om-call { font-family:'IBM Plex Mono',monospace; font-size:.75rem; color:__MUTED__;
  background:#24282c; border:1px solid __LINE__; border-radius:8px;
  padding:7px 10px; margin-bottom:6px; }
.om-call b { color:__BLUE__; font-weight:500; }
</style>
"""

for _k, _v in {
    "__BG__": BG, "__SURFACE__": SURFACE, "__LINE__": LINE, "__TEXT__": TEXT,
    "__MUTED__": MUTED, "__MINT__": MINT, "__BLUE__": BLUE, "__AMBER__": AMBER,
}.items():
    CSS = CSS.replace(_k, _v)


def apply(page_title: str, icon: str = "◆", wide: bool = True) -> None:
    st.set_page_config(
        page_title="OpsMind - " + page_title,
        page_icon=icon,
        layout="wide" if wide else "centered",
        initial_sidebar_state="expanded",
    )
    st.markdown(CSS, unsafe_allow_html=True)


def kicker(text: str) -> None:
    st.markdown('<div class="om-kicker">' + text + '</div>', unsafe_allow_html=True)


def card(html: str) -> None:
    st.markdown('<div class="om-card">' + html + '</div>', unsafe_allow_html=True)


def tag(label: str, live: bool) -> str:
    cls = "om-live" if live else "om-mock"
    state = "live" if live else "mock"
    return '<span class="om-tag ' + cls + '">' + label + " - " + state + "</span>"


def capability_bar(h: dict | None) -> None:
    if not h:
        st.error("API unreachable. Start it with: uvicorn app.main:app --reload")
        return
    c = h.get("capabilities", {})
    vs = h.get("vector_store", {})
    st.markdown(
        tag(h.get("model", "model"), c.get("gemini", False))
        + tag("mongo - " + str(h.get("datastore", {}).get("mode", "?")), c.get("mongo", False))
        + tag("vectors - " + str(vs.get("chunks", 0)) + " chunks", c.get("supabase_vectors", False))
        + tag("celery", bool(h.get("celery_broker")))
        + tag("auth - " + str(h.get("auth_mode", "?")), c.get("firebase_auth", False)),
        unsafe_allow_html=True,
    )


def render_citations(citations: list[dict]) -> None:
    if not citations:
        return
    kicker("sources")
    for i, c in enumerate(citations, 1):
        st.markdown(
            '<div class="om-cite">[' + str(i) + "] <b>" + str(c.get("title")) + "</b> - chunk "
            + str(c.get("chunk_index")) + " - score " + str(c.get("score")) + "<br />"
            + str(c.get("snippet", ""))[:300] + "...</div>",
            unsafe_allow_html=True,
        )


def render_tool_calls(calls: list[dict]) -> None:
    if not calls:
        return
    kicker("tool trace")
    for c in calls:
        st.markdown(
            '<div class="om-call"><b>' + str(c.get("name")) + "</b> " + str(c.get("args"))
            + " - " + str(c.get("result_summary")) + " - " + str(c.get("duration_ms", 0)) + "ms"
            + (" OK" if c.get("ok") else " FAILED") + "</div>",
            unsafe_allow_html=True,
        )


def boot(page_title: str):
    """Standard page header. Returns the health payload."""
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent))
    apply(page_title)
    return None
