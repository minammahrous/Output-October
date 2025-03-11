import streamlit as st
import psycopg2

def get_db_connection():
    """Establish a connection to the PostgreSQL database"""
    try:
        db_user = st.secrets["database"]["user"]
        db_name = st.secrets["database"]["database"]
        branch = st.session_state.get("branch", "main")  # Default to 'main'
        db_host = st.secrets["database"]["hosts"].get(branch)
        db_password = st.secrets["branch_passwords"].get(branch)

        if not db_host or not db_password:
            raise ValueError("Invalid database host or missing branch password.")

        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=5432
        )

        return conn

    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None  # Return None if the connection fails
