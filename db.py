import streamlit as st
import psycopg2

def get_db_connection():
    # Determine the correct branch
    branch = st.session_state.get("branch", "main")

    conn = psycopg2.connect(
        dbname=st.secrets["database"]["dbname"],
        user=st.secrets["database"]["user"],
        password=st.secrets["database"]["password"],
        host=st.secrets["database"]["host"],
        options=f"-c search_path={branch}"
    )
    return conn
