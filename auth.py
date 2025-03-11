import streamlit as st
import bcrypt
from db import get_db_connection  # Ensure this is imported AFTER defining functions

# Role-based access
ROLE_ACCESS = {
    "admin": ["shift_output_form", "reports_dashboard", "master_data"],
    "power user": ["shift_output_form", "reports_dashboard"],
    "user": ["shift_output_form"],
    "report": ["reports_dashboard"],
}

def authenticate_user():
    """Authenticate user and return user details"""
    if "user" in st.session_state:
        return st.session_state["user"]

    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username", key="login_username")
    password = st.sidebar.text_input("Password", type="password", key="login_password")
    login_btn = st.sidebar.button("Login")

    if login_btn:
        conn = get_db_connection()
        if not conn:
            st.sidebar.error("Database connection failed.")
            return None
        
        cur = conn.cursor()
        cur.execute("SELECT username, password, role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode(), user[1].encode()):
            st.session_state["user"] = {"username": user[0], "role": user[2]}
            st.session_state["branch"] = "main"  # Assign default branch
            st.rerun()
        else:
            st.sidebar.error("Invalid username or password")

    return None
