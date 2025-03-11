from sqlalchemy import create_engine, text
import streamlit as st

# Load database credentials from Streamlit secrets
BRANCH_CREDENTIALS = st.secrets["branch_credentials"]  # Dictionary with host & password per branch
DB_USER = st.secrets["database"]["user"]
DB_NAME = st.secrets["database"]["database"]

def get_db_connection():
    """Returns a database connection for the selected branch."""
    branch = st.session_state.get("branch", "main")  # Default to 'main'

    # Get credentials for the selected branch
    branch_data = BRANCH_CREDENTIALS.get(branch, None)

    if not branch_data:
        st.error(f"⚠️ No credentials found for branch '{branch}'")
        return None

    DB_HOST = branch_data["host"]
    DB_PASSWORD = branch_data["password"]

    # Construct database URL
    db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?sslmode=require"

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        conn = engine.connect()
        st.write(f"DEBUG: Connected to → {DB_HOST}")  # ✅ Print which DB is used
        return conn
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return None

def get_branches():
    """Fetch available branches from the database."""
    try:
        with get_db_connection() as conn:
            if conn:
                result = conn.execute(text("SELECT branch_name FROM branches"))
                return [row[0] for row in result.fetchall()]
    except Exception as e:
        st.error(f"Failed to fetch branches: {e}")
        return ["main"]  # Fallback to 'main'

# Streamlit UI: Branch selection
selected_branch = st.selectbox("Select a branch", list(BRANCH_CREDENTIALS.keys()))
st.session_state["branch"] = selected_branch  # Save in session state

# Attempt connection
connection = get_db_connection()
if connection:
    st.success(f"✅ Connected to {selected_branch} branch successfully!")
