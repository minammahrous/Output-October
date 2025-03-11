from sqlalchemy import create_engine
import streamlit as st

# Database connection URL (Replace with your actual credentials)
DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"

# Create the engine with connection pooling
engine = create_engine(DB_URL, pool_pre_ping=True)

def get_db_connection():
    """Returns a new database connection."""
    return engine.connect()
