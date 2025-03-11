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
    db_password = BRANCH_PASSWORDS.get(branch, BRANCH_PASSWORDS["main"])  # Default to 'main' password
    db_host = DB_HOSTS.get(branch, DB_HOSTS["main"])  # Get branch-specific host

    # Modify database name dynamically if a different branch is selected
    db_name = f"{DB_NAME}_{branch}" if branch != "main" else DB_NAME

    # Construct the database URL securely with search_path set to "public"
    db_url = f"postgresql://{DB_USER}:{db_password}@{db_host}/{db_name}?sslmode=require&options=-csearch_path=public"

    try:
        engine = create_engine(db_url, pool_pre_ping=True)
        conn = engine.connect()
        st.write(f"DEBUG: Connected to → {db_host} (DB: {db_name})")  # ✅ Print which DB and host are used

        # Debug: Print current database and schema
        result = conn.execute(text("SELECT current_database(), current_schema();"))
        st.write(f"DEBUG: Current DB & Schema → {result.fetchall()}")  

        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def get_branches():
    """Fetch available branches from the database."""
    try:
        with get_db_connection() as conn:
            result = conn.execute(text("SELECT branch_name FROM public.branches"))
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
