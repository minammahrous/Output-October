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

# Debugging
st.write("Selected Date:", date_selected)
st.write("Selected Shift:", shift_selected)

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

query_production = """
    SELECT 
        "Machine", 
        "batch number",  
        SUM("quantity") AS "Produced Quantity",
        (SELECT SUM("quantity") 
         FROM archive 
         WHERE archive."Machine" = a."Machine" 
         AND archive."batch numbe" = a."batch numbe" 
         AND archive."Activity" = 'Production') AS "Total Batch Quantity"
    FROM archive a
    WHERE "Activity" = 'Production' AND "Date" = %(date)s AND "Day/Night/plan" = %(shift)s
    GROUP BY "Machine", "Batch"
    ORDER BY "Machine", "Batch";
"""

# Fetch data
df_av = get_data(query_av, {"date": date_selected, "shift": shift_selected})
df_archive = get_data(query_archive, {"date": date_selected, "shift": shift_selected})
df_production = get_data(query_production, {"date": date_selected, "shift": shift_selected})

# Debugging: Check if DataFrames have data
st.write("AV Table Size:", df_av.shape)
st.write("Archive Table Size:", df_archive.shape)
st.write("Production Table Size:", df_production.shape)

# Ensure DataFrame is not empty
if not df_av.empty:
    st.subheader("Machine Efficiency, Availability & OEE")
    fig = px.bar(df_av, x="machine", y=["Availability", "Av Efficiency", "OEE"], 
                 barmode='group', title="Performance Metrics per Machine")
    st.plotly_chart(fig)
else:
    st.warning("No AV data available for the selected filters.")

# Display Archive Data
st.subheader("Machine Activity Summary")
st.dataframe(df_archive)

# Display Production Summary
st.subheader("Production Summary per Machine")
st.dataframe(df_production)

