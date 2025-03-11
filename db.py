from sqlalchemy import create_engine, text
import streamlit as st

# Base Database URL (Connects to 'main' by default)
BASE_DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

def get_db_connection():
    """Returns a database connection for the selected branch."""
    branch = st.session_state.get("branch", "main")  # Default to 'main' if not set

    # Modify database URL dynamically if a different branch is selected
    if branch != "main":
        db_url = BASE_DB_URL.replace("neondb", f"neondb_{branch}")
    else:
        db_url = BASE_DB_URL

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        conn = engine.connect()
        st.write(f"DEBUG: Connected to → {db_url}")  # ✅ Print which DB is used
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
