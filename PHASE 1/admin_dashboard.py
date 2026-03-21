import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(page_title="Admin Dashboard", layout="wide")
st.title("📊 Internal Admin Dashboard")

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

# ----------------------------- Tabs -----------------------------
tab1, tab2, tab3 = st.tabs(
    ["📋 Data View", "➕ Action Panel", "📈 Analytics"]
)

# Global container for user data
users_df = pd.DataFrame()

# ----------------------------- TAB 1: Data View -----------------------------
with tab1:
    st.subheader("User Database")
    try:
        res = requests.get(f"{API_BASE}/users")
        res.raise_for_status()
        data = res.json()
        users_df = pd.DataFrame(data)

        if not users_df.empty:
            # FIX: Added format='ISO8601' to handle the "T" in the timestamp
            users_df["created_at"] = pd.to_datetime(users_df["created_at"], format='ISO8601')
            
            st.dataframe(users_df.sort_values("created_at", ascending=False), use_container_width=True)
        else:
            st.info("System is ready. No users found yet.")

    except requests.exceptions.ConnectionError:
        st.error("⚠️ Connection refused: Make sure api.py is running.")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

# ----------------------------- TAB 2: Action Panel -----------------------------
with tab2:
    st.subheader("Add New User")
    with st.form("add_user_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        submitted = st.form_submit_button("Add User")
        
        if submitted:
            if not name or not email:
                st.error("All fields are required.")
            else:
                # Auto-increment ID based on current data
                new_id = 1
                if not users_df.empty and "id" in users_df.columns:
                    try:
                        new_id = int(users_df["id"].max()) + 1
                    except:
                        new_id = 1
                
                payload = {"id": new_id, "name": name, "email": email}
                
                try:
                    res = requests.post(f"{API_BASE}/users/onboard", json=payload)
                    res.raise_for_status()
                    st.success("User added successfully!")
                    st.rerun() # Refresh to show new user in Tab 1
                except requests.exceptions.HTTPError:
                    st.error(res.json().get("detail", "Error adding user"))
                except Exception as e:
                    st.error(f"Error: {e}")

# ----------------------------- TAB 3: Analytics -----------------------------
with tab3:
    st.subheader("User Growth Over Time")
    if not users_df.empty:
        try:
            # Copy to avoid modifying the original view
            df_analytics = users_df.copy()
            
            # Ensure it's datetime (in case Tab 1 failed or skipped)
            # using 'mixed' here is safest for analytics if data sources vary
            df_analytics["created_at"] = pd.to_datetime(df_analytics["created_at"], format='mixed')
            
            df_analytics["date"] = df_analytics["created_at"].dt.date
            
            growth_df = df_analytics.groupby("date").size().cumsum().reset_index(name="total_users")
            st.line_chart(growth_df.set_index("date"), height=400)
        except Exception as e:
            st.error(f"Analytics error: {e}")
    else:
        st.warning("Not enough data to display analytics.")