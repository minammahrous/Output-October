import streamlit as st
from sqlalchemy import create_engine, text
# Database connection

def get_db_connection():
    """Return a database connection based on the selected branch."""
    base_url = postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
    branch = st.session_state.get("branch", "main")  # Default to 'main' if not set
    
    # Modify DB URL to use the correct branch
    db_url = base_url.replace("neondb", f"neondb_{branch}") if branch else base_url
    
    engine = create_engine(db_url, pool_pre_ping=True)
    return engine.connect()
