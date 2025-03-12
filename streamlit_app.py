import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))  # Ensure modules are found

from auth import authenticate_user, ROLE_ACCESS
from db import get_branches

# Authenticate user
user = authenticate_user()
if not user:
    st.warning("Authentication failed. Please log in again.")
    st.stop()

# Set session state for authentication
st.session_state["authenticated"] = True
st.session_state["role"] = user.get("role", "user")
st.session_state["branch"] = user.get("branch", "main")
# Store role and branch in session state
st.session_state["role"] = role
st.session_state["branch"] = user_branch

# Admins can select a branch
if role == "admin":
    branches = get_branches()
    selected_branch = st.selectbox(
        "Select a branch:", branches, 
        index=branches.index(st.session_state["branch"]) if st.session_state["branch"] in branches else 0
    )

    if selected_branch != st.session_state["branch"]:
        st.session_state["branch"] = selected_branch
        st.rerun()

# Display UI
st.title("Welcome to the App")
st.write("Use the sidebar to navigate.")
st.write(f"DEBUG: User Role → {role}")
st.write(f"DEBUG: Assigned Branch → {st.session_state['branch']}")

# Define accessible pages based on role
allowed_pages = ROLE_ACCESS.get(role, [])

# Navigation links
if "shift_output_form" in allowed_pages:
    st.page_link("pages/shift_output_form.py", label="Shift Output Form")

if "reports_dashboard" in allowed_pages:
    st.page_link("pages/reports_dashboard.py", label="Reports Dashboard")

if "master_data" in allowed_pages:
    st.page_link("pages/master_data.py", label="Master Data Control")

# Success message
st.success(f"Now working on: {st.session_state['branch']}")
