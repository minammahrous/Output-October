from sqlalchemy import create_engine, text
import streamlit as st

# Base Database URL (Always connects to 'main' by default)
DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

# Create engine for main branch
engine = create_engine(DB_URL, pool_pre_ping=True)

def get_db_connection():
    """Returns a database connection for the selected branch."""
    branch = st.session_state.get("branch", "main")  # Default to 'main' if not set

    if branch == "main":
        db_url = DB_URL
    else:
        db_url = DB_URL.replace("neondb", f"neondb_{branch}")  # Switch to other branches

    try:
        branch_engine = create_engine(db_url, pool_pre_ping=True)
        return branch_engine.connect()
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def get_branches():
    """Fetch available branches from the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT branch_name FROM branches"))  # Adjust if needed
            return [row[0] for row in result.fetchall()]
    except Exception as e:
        st.error(f"Failed to fetch branches: {e}")
        return ["main"]
