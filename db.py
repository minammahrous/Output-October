import streamlit as st
from sqlalchemy import create_engine, text

def get_db_connection():
    """Return a database connection based on the selected branch."""
    base_url = st.secrets["database"]["url"]  # Read from Streamlit secrets
    branch = st.session_state.get("branch", "main")  # Default to 'main' if not set
    
    # Modify DB URL to use the correct branch
    db_url = base_url.replace("neondb", f"neondb_{branch}") if branch else base_url
    
    engine = create_engine(db_url, pool_pre_ping=True)
    return engine.connect()
