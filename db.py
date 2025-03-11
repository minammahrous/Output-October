from sqlalchemy import create_engine, text
import streamlit as st

# Load database credentials from Streamlit secrets
DB_HOSTS = st.secrets["database"]["hosts"]  # Dictionary: {branch_name: host}
DB_NAME = st.secrets["database"]["database"]
DB_USER = st.secrets["database"]["user"]
BRANCH_PASSWORDS = st.secrets["branch_passwords"]  # Dictionary of passwords for each branch

def get_db_connection():
    """Returns a database connection for the selected branch."""
    branch = st.session_state.get("branch", "main")  # Default to 'main' if not set

    # Get the correct password and host for the selected branch
    db_password = BRANCH_PASSWORDS.get(branch)
    db_host = DB_HOSTS.get(branch)

    if not db_password or not db_host:
        st.error(f"⚠️ No credentials found for branch '{branch}'. Check Streamlit secrets.")
        return None

    # ✅ Removed search_path from connection string
    db_url = f"postgresql://{DB_USER}:{db_password}@{db_host}/{DB_NAME}?sslmode=require"

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        conn = engine.connect()
        st.write(f"✅ Connected to → {db_host} (DB: {DB_NAME})")
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

def get_branches():
    """Fetch available branches from the database."""
    try:
        with get_db_connection() as conn:
            if conn:
                result = conn.execute(text("SELECT branch_name FROM public.branches"))
                return [row[0] for row in result.fetchall()]
    except Exception as e:
        st.error(f"Failed to fetch branches: {e}")
        return ["main"]  # Fallback to 'main'

# Streamlit UI: Branch selection
selected_branch = st.selectbox("Select a branch", list(BRANCH_PASSWORDS.keys()))
st.session_state["branch"] = selected
