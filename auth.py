import streamlit as st
from sqlalchemy import text
from db import get_db_connection

# Define role-based access control
ROLE_ACCESS = {
    "admin": ["shift_output_form", "reports_dashboard", "master_data"],
    "report": ["reports_dashboard"],
    "user": ["shift_output_form", "reports_dashboard"],
    "power_user": ["shift_output_form", "reports_dashboard", "master_data"]
}

def get_user(username, password):
    """Fetch user data from the database."""
    try:
        with get_db_connection() as conn:
            query = text("SELECT username, role, branch FROM users WHERE username=:username AND password=:password")
            result = conn.execute(query, {"username": username, "password": password}).fetchone()

        if result:
            return {"username": result[0], "role": result[1], "branch": result[2]}
        return None
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def authenticate_user():
    """Streamlit login form and session management."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")

        if login_button:
            user = get_user(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.username = user["username"]
                st.session_state.role = user["role"]
                st.session_state.branch = user["branch"]  # Can be 'all' for admin-like users
                st.success(f"Welcome, {user['username']}!")
                st.rerun()  # ✅ Fix: Use st.rerun() instead of st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    return st.session_state.authenticated
