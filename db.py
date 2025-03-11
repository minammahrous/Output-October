import streamlit as st
import psycopg2
import toml

# Load database secrets from Streamlit
db_secrets = st.secrets["database"]
DB_USER = db_secrets["user"]
DB_NAME = db_secrets["database"]
DB_HOSTS = db_secrets["hosts"]  # Dictionary: {branch_name: host}

def get_branches():
    """Returns a list of available database branches."""
    return list(DB_HOSTS.keys())

def get_db_connection():
    """Establish and return a database connection based on the user's assigned branch."""
    user_branch = st.session_state.get("branch", "main")  # Default to 'main'
    db_host = DB_HOSTS.get(user_branch, DB_HOSTS["main"])  # Default to main if not found

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            host=db_host,
            password=st.secrets["branch_passwords"].get(user_branch, ""),
            options="-c search_path=public"
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Database connection error: {str(e)}")
        return None
