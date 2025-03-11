import streamlit as st
from auth import authenticate_user, ROLE_ACCESS
from db import get_branches, get_db_connection

# Authenticate the user
if not authenticate_user():
    st.stop()

# Title and sidebar
st.title("Welcome to the App")
st.write("Use the sidebar to navigate.")

# Get user role and branch from session
role = st.session_state.get("role")
current_branch = st.session_state.get("branch")

# Fetch available branches (for admin role)
branches = get_branches()

# ✅ Only admins can select a branch
if role == "admin":
    selected_branch = st.selectbox("Select a branch:", branches, index=branches.index(current_branch) if current_branch in branches else 0)
    
    if selected_branch != current_branch:
        st.session_state["branch"] = selected_branch
        st.rerun()  # ✅ Force app refresh

st.success(f"Now working on: {st.session_state.get('branch', 'main')}")
st.write("DEBUG: Assigned Branch →", st.session_state.get("branch", "main"))

# Define accessible pages based on role
allowed_pages = ROLE_ACCESS.get(role, [])

# Navigation links
if "shift_output_form" in allowed_pages:
    st.page_link("pages/shift_output_form.py", label="Shift Output Form")

if "reports_dashboard" in allowed_pages:
    st.page_link("pages/reports_dashboard.py", label="Reports Dashboard")

if "master_data" in allowed_pages:
    st.page_link("pages/master_data.py", label="Master Data Control")
