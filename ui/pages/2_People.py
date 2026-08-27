"""Employee management: filter, onboard, offboard."""
import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

import theme
from api_client import ApiError, delete, get, post

theme.apply("People")
st.title("People")
st.caption("The same records the agent reads and writes through its tools.")

with st.sidebar:
    st.markdown("### Filters")
    role = st.selectbox("Role", ["any", "intern", "engineer", "manager", "admin"])
    dept = st.text_input("Department contains", "")
    only_active = st.toggle("Active only", value=True)
    limit = st.slider("Limit", 5, 200, 50)

params = {"limit": limit}
if role != "any":
    params["role"] = role
if only_active:
    params["active"] = True

try:
    people = get("/employees", **params)
except ApiError as exc:
    st.error(str(exc))
    st.stop()

if dept:
    people = [p for p in people if dept.lower() in (p.get("department") or "").lower()]

c1, c2, c3 = st.columns(3)
c1.metric("Shown", len(people))
c2.metric("Interns", sum(1 for p in people if p["role"] == "intern"))
c3.metric("Managers", sum(1 for p in people if p["role"] == "manager"))

if people:
    df = pd.DataFrame(people)[
        ["name", "email", "role", "department", "joined_on", "manager_email", "active"]
    ]
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    theme.card("No employees match those filters.")

st.divider()
left, right = st.columns(2, gap="large")

with left:
    theme.kicker("onboard")
    with st.form("create"):
        name = st.text_input("Full name")
        email = st.text_input("Work email")
        new_role = st.selectbox("Role", ["intern", "engineer", "manager", "admin"])
        new_dept = st.text_input("Department", "platform")
        joined = st.date_input("Joined on", value=date.today())
        manager = st.text_input("Manager email", "")
        if st.form_submit_button("Create record"):
            try:
                res = post("/employees", json={
                    "name": name, "email": email, "role": new_role,
                    "department": new_dept, "joined_on": joined.isoformat(),
                    "manager_email": manager or None, "active": True,
                })
                st.success("Created " + res["name"])
                st.rerun()
            except ApiError as exc:
                st.error(str(exc))

with right:
    theme.kicker("offboard")
    target = st.selectbox("Employee", [p["email"] for p in people] or ["-"])
    st.caption("Deactivates the record and writes an audit entry. Nothing is hard-deleted.")
    if st.button("Deactivate") and target != "-":
        try:
            delete("/employees/" + target)
            st.success("Deactivated " + target)
            st.rerun()
        except ApiError as exc:
            st.error(str(exc))
