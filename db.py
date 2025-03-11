from sqlalchemy import create_engine, text
import streamlit as st

# Load database credentials from Streamlit secrets
DB_HOST = st.secrets["database"]["host"]
DB_NAME = st.secrets["database"]["database"]
DB_USER = st.secrets["database"]["user"]
BRANCH_PASSWORDS = st.secrets["branch_passwords"]  # Dictionary of passwords for each branch

def get_db_connection():
    """Returns a database connection for the selected branch."""
    branch = st.session_state.get("branch", "main")  # Default to 'main' if not set

    # Get the correct password for the selected branch
    db_password = BRANCH_PASSWORDS.get(branch, BRANCH_PASSWORDS["main"])  # Default to 'main' password

    # Modify database name dynamically if a different branch is selected
    db_name = f"{DB_NAME}_{branch}" if branch != "main" else DB_NAME

    # Construct the database URL securely
    db_url = f"postgresql://{DB_USER}:{db_password}@{DB_HOST}/{db_name}?sslmode=require"

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        conn = engine.connect()
        st.write(f"DEBUG: Connected to → {db_name}")  # ✅ Print which DB is used
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
        return ["main"]  # Return at least 'main' as a fallback

# Streamlit UI: Branch selection
selected_branch = st.selectbox("Select a branch", list(BRANCH_PASSWORDS.keys()))
st.session_state["branch"] = selected_branch  # Save the selected branch in session state

# Attempt connection when the user selects a branch
connection = get_db_connection()
if connection:
    st.success(f"Connected to {selected_branch} branch successfully!")
