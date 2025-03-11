import streamlit as st
from auth import authenticate_user, ROLE_ACCESS
from db import get_db_connection

# Authenticate the user
if not authenticate_user():
    st.stop()

# Title and sidebar
st.title("Welcome to the App")
st.write("Use the sidebar to navigate.")

# Get user role and branch from session
role = st.session_state.get("role")
branch = st.session_state.get("branch", "main")  # Default to 'main' if not set

# Fetch available branches
branches = get_branches()

# Allow admin or "all" branch users to select a branch
if role == "admin" or branch == "all":
    selected_branch = st.selectbox("Select a branch:", branches, index=0)
    
    # Update session state when selection changes
    if selected_branch != st.session_state.get("branch"):
        st.session_state.branch = selected_branch
        st.rerun()  # ✅ Force update when branch changes

    st.success(f"Now working on: {selected_branch}")
else:
    st.info(f"Current branch: {branch}")  # Show the assigned branch for non-admin users

# Define accessible pages based on role
allowed_pages = ROLE_ACCESS.get(role, [])

# Navigation links
if "shift_output_form" in allowed_pages:
    st.page_link("pages/shift_output_form.py", label="Shift Output Form")

if "reports_dashboard" in allowed_pages:
    st.page_link("pages/reports_dashboard.py", label="Reports Dashboard")

if "master_data" in allowed_pages:
    st.page_link("pages/master_data.py", label="Master Data Control")
