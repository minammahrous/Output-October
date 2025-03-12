import streamlit as st
from auth import authenticate_user, ROLE_ACCESS
from db import get_branches

# Authenticate user
user = authenticate_user()

if not user:  # Prevent undefined variable errors
    st.warning("Authentication failed. Please log in again.")
    st.stop()

# Retrieve role and branch safely
st.session_state["authenticated"] = True
st.session_state["username"] = user["username"]
st.session_state["role"] = user.get("role", "user")  # Default to "user"
st.session_state["branch"] = user.get("branch", "main")  # Default branch is "main"

# Admins can select a branch
if st.session_state["role"] == "admin":
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
st.write(f"DEBUG: User Role → {st.session_state['role']}")
st.write(f"DEBUG: Assigned Branch → {st.session_state['branch']}")

# Define accessible pages based on role
allowed_pages = ROLE_ACCESS.get(st.session_state["role"], [])

# Navigation links
if "shift_output_form" in allowed_pages:
    st.page_link("pages/shift_output_form.py", label="Shift Output Form")

if "reports_dashboard" in allowed_pages:
    st.page_link("pages/reports_dashboard.py", label="Reports Dashboard")

if "master_data" in allowed_pages:
    st.page_link("pages/master_data.py", label="Master Data Control")
    
if "user management" in allowed_pages:
    st.page_link("pages/user_management.py", label="User Management")
# Success message
st.success(f"Now working on: {st.session_state['branch']}")
