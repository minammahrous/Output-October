import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import text
from db import get_sqlalchemy_engine
from auth import check_authentication, check_access

# ✅ Authenticate and enforce role-based access
check_authentication()
check_access(["user", "power user", "admin", "report"])

# ✅ Get database engine
engine = get_sqlalchemy_engine()

# ✅ Function to Fetch Data from PostgreSQL
def get_data(query, params=None):
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return pd.DataFrame()

# ✅ Streamlit UI
st.title("📊 Machine Performance Dashboard")

# ✅ User Inputs: Single Date or Date Range Selection
date_option = st.radio("📅 Select Report Type", ["Single Date", "Date Range"])

if date_option == "Single Date":
    selected_date = st.date_input("📅 Select Date")
    start_date, end_date = selected_date, selected_date
    shift_selected = st.selectbox("🕒 Select Shift Type", ["Day", "Night", "Plan"])
    shift_filter = 'AND "Day/Night/plan" = :shift'
else:
    date_range = st.date_input("📅 Select Date Range", [pd.to_datetime("today"), pd.to_datetime("today")])

    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        st.warning("Please select both start and end dates.")
        st.stop()
    
    shift_selected = None  # No shift filtering in date range mode
    shift_filter = ""  # Includes all shifts

# ✅ SQL Query to Fetch Production Data
query_production = f"""
    SELECT 
        "Machine", 
        "batch number",  
        a."Product" AS "Product",  
        SUM("quantity") AS "Produced Quantity",
        SUM(SUM("quantity")) OVER (PARTITION BY "Machine", "batch number") AS "Total Batch Output"
    FROM archive a
    WHERE "Activity" = 'Production' 
        AND "Date" BETWEEN :start_date AND :end_date
        {shift_filter}
    GROUP BY "Machine", "batch number", a."Product"
    ORDER BY "Machine", "batch number";
"""

# ✅ Set Query Parameters
params = {"start_date": start_date, "end_date": end_date}
if shift_selected:
    params["shift"] = shift_selected

# ✅ Fetch Data
df_production = get_data(query_production, params)

# ✅ Display Production Summary Table
st.subheader("🏭 Production Summary per Machine and Batch")
st.dataframe(df_production)
