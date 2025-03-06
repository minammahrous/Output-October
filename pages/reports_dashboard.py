import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# Database connection
DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
engine = create_engine(DB_URL)

def get_data(query, params=None):
    """Fetch data from Neon PostgreSQL using SQLAlchemy."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return pd.DataFrame()

# Streamlit UI
st.title("Machine Performance Dashboard")

# User inputs
date_selected = st.date_input("Select Date")
shift_selected = st.selectbox("Select Shift Type", ["Day", "Night", "Plan"])

# Queries
query_av = """
    SELECT "machine", "Availability", "Av Efficiency", "OEE"
    FROM av
    WHERE "date" = %(date)s AND "shift type" = %(shift)s
"""

query_archive = """
    SELECT "Machine", "Activity", SUM("time") as "Total_Time", AVG("efficiency") as "Avg_Efficiency"
    FROM archive
    WHERE "Date" = %(date)s AND "Day/Night/plan" = %(shift)s
    GROUP BY "Machine", "Activity"
"""

# Production Summary Query (Extracting from archive table)
query_production = """
    SELECT 
        a."Machine", 
        a."Batch Number", 
        SUM(a."Qty") AS "Produced Quantity",
        (SELECT SUM("Qty") 
         FROM archive 
         WHERE "Machine" = a."Machine" 
         AND "Batch Number" = a."Batch Number" 
         AND "Activity" = 'Production') AS "Total Batch Quantity"
    FROM archive a
    WHERE a."Date" = %(date)s 
    AND a."Day/Night/plan
    """
