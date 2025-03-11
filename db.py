from sqlalchemy import create_engine, text
import streamlit as st

# Base Database URL (Always starts with 'main')
BASE_DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

def get_db_connection():
    """Returns a database connection for the selected branch."""
    branch = st.session_state.get("branch", "main")  # Default to 'main' if not set

    # Ensure the correct database name is used
    if branch != "main":
        db_url = BASE_DB_URL.replace("neondb", f"neondb_{branch}")
    else:
        db_url = BASE_DB_URL  # Keep 'main' as is

    try:
        branch_engine = create_engine(db_url, pool_pre_ping=True)
        conn = branch_engine.connect()
        st.write(f"DEBUG: Connected to → {db_url}")  # ✅ Debug Output
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def get_branches():
    """Fetch available branches from the database."""
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT branch_name FROM branches"))
            return [row[0] for row in result.fetchall()]
    except Exception as e:
        st.error(f"Failed to fetch branches: {e}")
        return ["main"]
