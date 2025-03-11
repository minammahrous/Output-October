import streamlit as st
import psycopg2
from sqlalchemy import create_engine
import streamlit as st

def get_sqlalchemy_engine():
    """Returns a SQLAlchemy engine for connecting to the correct PostgreSQL branch."""
    
    # Get the user's assigned branch from session state
    branch = st.session_state.get("branch", "main")  # Default to "main"

    # Load database host from secrets based on the branch
    db_host = st.secrets["database"]["hosts"].get(branch, st.secrets["database"]["hosts"]["main"])
    db_user = st.secrets["database"]["user"]
    db_password = st.secrets["branch_passwords"].get(branch, st.secrets["branch_passwords"]["main"])
    db_name = st.secrets["database"]["database"]  # Same database name, different branches

    # ✅ Construct the database URL dynamically
    db_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"

    return create_engine(db_url, pool_pre_ping=True)
def get_db_connection():
    """Establish and return a database connection based on the user's assigned branch."""
    try:
        db_user = st.secrets["database"]["user"]
        db_name = st.secrets["database"]["database"]
        branch = st.session_state.get("branch", "main")  # Default to 'main'
        db_host = st.secrets["database"]["hosts"].get(branch)
        db_password = st.secrets["branch_passwords"].get(branch)

        if not db_host or not db_password:
            st.error("Invalid database host or missing password.")
            return None

        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=5432
        )

        return conn

    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None  # Return None if connection fails

def get_branches():
    """Fetch available branches from the database."""
    conn = get_db_connection()
    if not conn:
        return ["main"]  # Fallback to 'main' if DB connection fails
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT branch_name FROM public.branches")  # Explicit schema
        branches = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return branches
    except Exception as e:
        st.error(f"Failed to fetch branches: {e}")
        return ["main"]
