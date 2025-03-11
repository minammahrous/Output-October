from sqlalchemy import create_engine, text

# Base Database URL (Main connection)
DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
engine = create_engine(DB_URL, pool_pre_ping=True)

def get_db_connection(branch="main"):
    """Returns a database connection for a specific branch."""
    if branch == "main":
        db_url = DB_URL
    else:
        db_url = DB_URL.replace("neondb", f"neondb_{branch}")  # Modify URL for branches
    
    branch_engine = create_engine(db_url, pool_pre_ping=True)
    return branch_engine.connect()

def get_branches():
    """Fetches available branches from Neon DB (assuming stored in a table)."""
    try:
        conn = engine.connect()
        query = text("SELECT branch_name FROM branches")  # Replace with actual query
        result = conn.execute(query).fetchall()
        conn.close()
        return [row[0] for row in result]
    except Exception as e:
        print(f"Failed to fetch branches: {e}")
        return ["main"]
