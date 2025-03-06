import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

# Database connection
Database connection
DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
engine = create_engine(DB_URL)

def get_data(query, params=None):
    """Fetch data from Neon PostgreSQL."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        df = pd.read_sql(query, conn, params=params)
    return df

# Streamlit UI
st.title("Machine Performance Dashboard")

# User inputs
date_selected = st.date_input("Select Date")
shift_selected = st.selectbox("Select Shift Type", ["Day", "Night", "Plan"])

# Queries
query_av = """
    SELECT machine, Availability, "Av Efficiency", OEE 
    FROM av 
    WHERE date = %s AND "shift type" = %s
"""
query_archive = """
    SELECT Machine, Activity, SUM(time) as Total_Time, AVG(efficiency) as Avg_Efficiency
    FROM archive
    WHERE Date = %s AND "Day/Night/plan" = %s
    GROUP BY Machine, Activity
"""

# Fetch data
df_av = get_data(query_av, (date_selected, shift_selected))
df_archive = get_data(query_archive, (date_selected, shift_selected))

# Display Archive Data
st.subheader("Machine Activity Summary")
st.dataframe(df_archive)

# Visualization - AV Table Data
if not df_av.empty:
    st.subheader("Machine Efficiency, Availability & OEE")
    fig = px.bar(df_av, x="machine", y=["Availability", "Av Efficiency", "OEE"], 
                 barmode='group', title="Performance Metrics per Machine")
    st.plotly_chart(fig)
else:
    st.warning("No data available for the selected filters.")

