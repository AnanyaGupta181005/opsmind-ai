"""Background work: Celery jobs, browser automation, n8n webhooks."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

import theme
from api_client import ApiError, get, post

theme.apply("Workflows")
st.title("Workflows")
st.caption("Async jobs, browser automation and external orchestration - with the runner named.")

try:
    health = get("/health")
    tasks = get("/tasks")
except ApiError as exc:
    st.error(str(exc))
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Runs recorded", len(tasks))
c2.metric("Broker", "celery" if health.get("celery_broker") else "inline")
c3.metric("Done", sum(1 for t in tasks if t.get("state") == "done"))

tab_jobs, tab_web, tab_n8n = st.tabs(["Report jobs", "Browser tasks", "n8n"])

with tab_jobs:
    col_a, col_b = st.columns([1, 2])
    with col_a:
        period = st.radio("Period", ["month", "quarter"], horizontal=True)
        if st.button("Queue headcount report"):
            res = post("/tasks/report", json={"report": "headcount", "period": period})
            st.success("Queued on " + res["runner"] + " - " + res["state"])
            st.rerun()
        st.caption(
            "With Redis running the job goes to a Celery worker. Without it the job runs "
            "inline and says so - no silent no-op."
        )
    with col_b:
        theme.kicker("run history")
        if tasks:
            st.dataframe(
                pd.DataFrame(tasks)[["kind", "state", "detail", "submitted_at"]],
                use_container_width=True, hide_index=True,
            )
            latest = [t for t in tasks if t.get("result")]
            if latest:
                with st.expander("Latest report payload"):
                    st.json(latest[-1]["result"])
        else:
            theme.card("No runs yet.")

with tab_web:
    st.markdown("Fetch a page with Playwright and capture its title and text.")
    url = st.text_input("URL", "https://example.com")
    if st.button("Run browser task"):
        try:
            res = post("/tasks/web", json={"url": url})
            st.json(res)
        except ApiError as exc:
            st.error(str(exc))
    theme.card(
        "Runs headless Chromium via Playwright. Install the browser once with "
        "<code>playwright install chromium</code>; if it is missing the endpoint reports that "
        "clearly instead of failing opaquely."
    )

with tab_n8n:
    st.markdown("Forward an event to an n8n workflow webhook.")
    event = st.text_input("Event name", "employee.onboarded")
    payload = st.text_area("Payload (JSON)", '{"email": "kabir@inbenne.com"}')
    if st.button("Send to n8n"):
        import json as _json

        try:
            res = post("/tasks/n8n", json={"event": event, "payload": _json.loads(payload)})
            st.success(str(res))
        except (ApiError, ValueError) as exc:
            st.error(str(exc))
    theme.card("Set <code>N8N_WEBHOOK_URL</code> in .env to enable this.")
