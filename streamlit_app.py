import streamlit as st
from auth import authenticate_user, ROLE_ACCESS

# Authenticate the user
if not authenticate_user():
    st.stop()

# Title and sidebar
st.title("Welcome to the App")
st.write("Use the sidebar to navigate.")

# Get user role and branch from session
role = st.session_state.get("role")
branch = st.session_state.get("branch")

# Allow admin or 'all' branch users to select a branch
if branch == "all":
    branch = st.selectbox("Select a branch:", ["branch1", "branch2", "branch3"])
    st.session_state.branch = branch  # Update session with selected branch
    st.success(f"Now working on: {branch}")

# Define available pages based on role
allowed_pages = ROLE_ACCESS.get(role, [])

# Navigation links
if "shift_output_form" in allowed_pages:
    st.page_link("pages/shift_output_form.py", label="Shift Output Form")

if "reports_dashboard" in allowed_pages:
    st.page_link("pages/reports_dashboard.py", label="Reports Dashboard")

if "master_data" in allowed_pages:
    st.page_link("pages/master_data.py", label="Master Data Control")
