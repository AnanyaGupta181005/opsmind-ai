"""Settings: what is live, what is mocked, and exactly how to switch each on."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import streamlit as st

import theme
from api_client import get, health

theme.apply("Settings")
st.title("Settings")
st.caption("Credentials are read from .env only - nothing is stored in the browser.")

h = health()
theme.capability_bar(h)
if not h:
    st.stop()

st.divider()
ROWS = [
    ("Gemini", "gemini", "GEMINI_API_KEY",
     "Function-calling agent, embeddings and Vision extraction.",
     "Falls back to a rule-based planner over the same tools."),
    ("MongoDB", "mongo", "MONGO_URI",
     "Employees, documents, chat turns, tasks and audit entries.",
     "Falls back to an in-process store seeded with six employees."),
    ("Supabase vectors", "supabase_vectors", "SUPABASE_URL + SUPABASE_SERVICE_KEY",
     "pgvector table policy_chunks with a cosine ivfflat index.",
     "Falls back to an in-process cosine index over the same chunks."),
    ("Firebase Auth", "firebase_auth", "FIREBASE_CREDENTIALS_JSON",
     "Bearer token verification with role claims.",
     "Dev bypass grants an admin identity - reported at /health."),
    ("n8n", "n8n", "N8N_WEBHOOK_URL",
     "Forwards operational events to external workflows.",
     "Endpoint returns 503 until configured."),
]

for label, key, env, live_desc, mock_desc in ROWS:
    on = h["capabilities"].get(key, False)
    theme.card(
        "<b>" + label + "</b> " + theme.tag(env, on)
        + "<br /><span class='om-kicker'>" + ("live" if on else "mock") + "</span>"
        + (live_desc if on else mock_desc)
    )

st.divider()
theme.kicker("runtime")
st.json({
    "auth_mode": h["auth_mode"],
    "model": h["model"],
    "datastore": h["datastore"],
    "vector_store": h["vector_store"],
    "celery_broker": h["celery_broker"],
    "env": h["env"],
    "version": h["version"],
})

theme.kicker("registered agent tools")
st.json(get("/agent/tools")["tools"])
