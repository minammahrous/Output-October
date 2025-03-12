import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import text
from db import get_sqlalchemy_engine
from auth import check_authentication, check_access
# Hide Streamlit's menu and "Manage app" button
st.markdown("""
    <style>
        [data-testid="stToolbar"] {visibility: hidden !important;}
        [data-testid="manage-app-button"] {display: none !important;}
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)
# ✅ Authenticate the user
check_authentication()

# ✅ Enforce role-based access (Allow "user", "power user", "admin", and "report")
check_access(["user", "power user", "admin", "report"])

# ✅ Get database engine for the user's assigned branch
engine = get_sqlalchemy_engine()

def get_data(query, params=None):
    """Fetch data from Neon PostgreSQL using SQLAlchemy."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return pd.DataFrame()

# ✅ Streamlit UI
st.title("📊 Machine Performance Dashboard")

# ✅ User inputs
date_selected = st.date_input("📅 Select Date")
shift_selected = st.selectbox("🕒 Select Shift Type", ["Day", "Night", "Plan"])

# Debugging
st.write(f"📝 **Selected Date:** {date_selected}")
st.write(f"📝 **Selected Shift:** {shift_selected}")

# ✅ Queries (Ensure safe parameter usage)
query_av = """
    SELECT "machine", "Availability", "Av Efficiency", "OEE"
    FROM av
    WHERE "date" = :date AND "shift" = :shift
"""

query_archive = """
    SELECT "Machine", "Activity", SUM("time") as "Total_Time", AVG("efficiency") as "Avg_Efficiency"
    FROM archive
    WHERE "Date" = :date AND "Day/Night/plan" = :shift
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
         AND archive."batch number" = a."batch number" 
         AND archive."Activity" = 'Production') AS "Total Batch Quantity"
    FROM archive a
    WHERE "Activity" = 'Production' AND "Date" = :date AND "Day/Night/plan" = :shift
    GROUP BY "Machine", "batch number"
    ORDER BY "Machine", "batch number";
"""

# ✅ Fetch data securely
df_av = get_data(query_av, {"date": date_selected, "shift": shift_selected})
df_archive = get_data(query_archive, {"date": date_selected, "shift": shift_selected})
df_production = get_data(query_production, {"date": date_selected, "shift": shift_selected})

# Debugging: Check if DataFrames have data
st.write(f"📊 **AV Table Size:** {df_av.shape}")
st.write(f"📊 **Archive Table Size:** {df_archive.shape}")
st.write(f"📊 **Production Table Size:** {df_production.shape}")

# ✅ Visualize AV Data
if not df_av.empty:
    st.subheader("📈 Machine Efficiency, Availability & OEE")
    fig = px.bar(df_av, x="machine", y=["Availability", "Av Efficiency", "OEE"], 
                 barmode='group', title="Performance Metrics per Machine")
    st.plotly_chart(fig)
else:
    st.warning("⚠️ No AV data available for the selected filters.")

# ✅ Display Archive Data
st.subheader("📋 Machine Activity Summary")
st.dataframe(df_archive)

# ✅ Display Production Summary
st.subheader("🏭 Production Summary per Machine")
st.dataframe(df_production)
