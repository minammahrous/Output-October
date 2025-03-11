import streamlit as st
from auth import authenticate_user, ROLE_ACCESS
from db import get_branches, get_db_connection

# Authenticate the user
user = authenticate_user()
if not user:
    st.stop()

# Title and sidebar
st.title("Welcome to the App")
st.write("Use the sidebar to navigate.")

# Get user role and branch from session state
role = user["role"]
user_branch = user.get("branch", "main")  # Default branch is "main"

# Ensure the branch is set in session state
if "branch" not in st.session_state:
    st.session_state["branch"] = user_branch

# Fetch available branches (for admins)
branches = get_branches()

# Admins can select a branch
if role == "admin":
    selected_branch = st.selectbox(
        "Select a branch:", branches, 
        index=branches.index(st.session_state["branch"]) if st.session_state["branch"] in branches else 0
    )

    # Update session state & refresh if branch changes
    if selected_branch != st.session_state["branch"]:
        st.session_state["branch"] = selected_branch
        st.rerun()

# Display the active branch
st.success(f"Now working on: {st.session_state['branch']}")

# Define accessible pages based on role
allowed_pages = ROLE_ACCESS.get(role, [])

# Navigation links
if "shift_output_form" in allowed_pages:
    st.page_link("pages/shift_output_form.py", label="Shift Output Form")

if "reports_dashboard" in allowed_pages:
    st.page_link("pages/reports_dashboard.py", label="Reports Dashboard")

if "master_data" in allowed_pages:
    st.page_link("pages/master_data.py", label="Master Data Control")
