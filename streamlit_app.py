import streamlit as st
import psycopg2
from db import get_db_connection

# App Title
st.title("Welcome to the App")
st.write("Use the sidebar to navigate.")

# Function to get user details from DB
def get_user(username, password):
    conn = psycopg2.connect(
        dbname=st.secrets["database"]["dbname"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        host=st.secrets["database"]["host"],
        options="-c search_path=main"
    )
    cur = conn.cursor()
    cur.execute("SELECT username, role, branch FROM users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    conn.close()
    
    if user:
        username, role, branch = user
        return {"username": username, "role": role, "branch": branch}  
    return None

# Login Form
if "authenticated" not in st.session_state:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        user = get_user(username, password)
        if user:
            st.session_state["authenticated"] = True
            st.session_state["username"] = user["username"]
            st.session_state["role"] = user["role"]
            st.session_state["branch"] = user["branch"]

            st.success(f"Welcome {user['username']}!")

            # If branch is "all", allow user to select a branch
            if user["branch"] == "all" or user["role"] == "admin":
                st.session_state["branch"] = st.selectbox(
                    "Select branch to work on:",
                    ["main", "Limitless"]  # Fetch dynamically if needed
                )

        else:
            st.error("Invalid credentials. Please try again.")

# Navigation Links (Show only if authenticated)
if "authenticated" in st.session_state and st.session_state["authenticated"]:
    st.title("Welcome to the App")
    st.write("Use the sidebar to navigate.")
    role = st.session_state["role"]

    if role in ["admin", "power user", "user"]:
        st.page_link("pages/shift_output_form.py", label="Shift Output Form")

    if role in ["admin", "power user", "report", "user"]:
        st.page_link("pages/reports_dashboard.py", label="Reports Dashboard")

    if role in ["admin", "power user"]:
        st.page_link("pages/master_data.py", label="Master Data Control")

st.title("Welcome to the App")
st.write("Use the sidebar to navigate.")

