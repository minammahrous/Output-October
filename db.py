import streamlit as st
from sqlalchemy import create_engine, text

def get_db_connection():
    """Return a database connection based on the user's selected branch."""
    base_url = st.secrets["database"]["url"]
    branch = st.session_state.get("branch", "main")  # Default to 'main' if not set
    
    # Modify DB URL to use the correct branch
    db_url = base_url.replace("neondb", f"neondb_{branch}") if branch else base_url
    
    engine = create_engine(db_url, pool_pre_ping=True)
    return engine.connect()

def get_branches():
    """Fetch available branches from the database."""
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT branch_name FROM branches"))
            branches = [row[0] for row in result.fetchall()]
        return branches
    except Exception as e:
        st.error(f"Failed to fetch branches: {e}")
        return []
