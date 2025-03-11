import streamlit as st
import psycopg2
import bcrypt
from db import get_db_connection

# Role-based access control
ROLE_ACCESS = {
    "admin": ["shift_output_form", "reports_dashboard", "master_data"],
    "user": ["shift_output_form", "reports_dashboard"],
    "power user": ["shift_output_form", "reports_dashboard", "master_data"],
    "report": ["reports_dashboard"],
}

def authenticate_user():
    """Handles user authentication and assigns branch based on database records."""
    
    if "authenticated" in st.session_state and st.session_state.authenticated:
        st.write("DEBUG: Already Authenticated →", st.session_state.username)
        return {
            "username": st.session_state.username,
            "role": st.session_state.role,
            "branch": st.session_state.branch,
        }

    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username", key="username_input")
    password = st.sidebar.text_input("Password", type="password", key="password_input")

    if st.sidebar.button("Login"):
        conn = get_db_connection()
        cur = conn.cursor()

        try:
            # Fetch user details
            cur.execute("SELECT username, password, role, branch FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

            st.write("DEBUG: Fetched User from DB →", user)  # Debugging

            if user:
                stored_password = user[1].strip()  # Ensure no extra spaces
                if bcrypt.checkpw(password.encode(), stored_password.encode()):
                    st.session_state.authenticated = True
                    st.session_state.username = user[0]
                    st.session_state.role = user[2]
                    st.session_state.branch = user[3]  # Assign branch from the users table
                    st.sidebar.success(f"Logged in as {user[0]} ({user[2]})")
                    
                    st.write("DEBUG: Login Successful!")
                    st.write("DEBUG: User Role →", user[2])
                    st.write("DEBUG: User Branch →", user[3])
                    
                    st.rerun()
                else:
                    st.sidebar.error("Invalid username or password")
                    st.write("DEBUG: Password Mismatch")

            else:
                st.sidebar.error("User not found")
                st.write("DEBUG: User Not Found in Database")

        except Exception as e:
            st.sidebar.error("Database error. Please try again.")
            st.write(f"DEBUG: Auth error → {e}")

        finally:
            cur.close()
            conn.close()

    return None  # Authentication failed
