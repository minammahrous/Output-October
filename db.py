import streamlit as st
from sqlalchemy import create_engine, text

# Get base DB URL from Streamlit secrets (Ensure it's correctly set in Streamlit Cloud)
BASE_DB_URL = st.secrets["database"]["url"]

def get_db_connection():
    """Returns a database connection based on the selected branch."""
    branch = st.session_state.get("branch", "main")  # Default to 'main'

    # Modify DB URL dynamically for different branches
    db_url = BASE_DB_URL.replace("neondb", f"neondb_{branch}") if branch != "main" else BASE_DB_URL

    engine = create_engine(db_url, pool_pre_ping=True)
    return engine.connect()
