import streamlit as st
import bcrypt
from db import get_db_connection

def authenticate_user():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Show login form if not authenticated
    if not st.session_state["authenticated"]:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT username, password, role FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            cur.close()
            conn.close()

            if user and bcrypt.checkpw(password.encode(), user[1].encode()):
                st.session_state["authenticated"] = True
                st.session_state["username"] = user[0]
                st.session_state["role"] = user[2]  # ✅ Store role
                st.success(f"Logged in as {user[0]}")
                st.rerun()  # ✅ Refresh app after login
            else:
                st.error("Invalid credentials")

    return st.session_state.get("authenticated", False)
