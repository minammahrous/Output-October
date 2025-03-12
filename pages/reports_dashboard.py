import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import text
from db import get_sqlalchemy_engine
from auth import check_authentication, check_access
import io
import plotly.io as pio
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from textwrap import wrap

# ✅ Hide Streamlit UI elements
st.markdown("""
    <style>
        [data-testid="stToolbar"] {visibility: hidden !important;}
        [data-testid="manage-app-button"] {display: none !important;}
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)

# ✅ Authenticate & enforce access control
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

# ✅ Report Type Selection
report_type = st.radio("📊 Select Report Type", ["Single Shift Report", "Date Range Report"])

# ✅ User Input Fields
if report_type == "Single Shift Report":
    date_selected = st.date_input("📅 Select Date")
    shift_selected = st.selectbox("🕒 Select Shift Type", ["Day", "Night", "Plan"])
    params = {"date": date_selected, "shift": shift_selected}
    file_suffix = f"{shift_selected}_{date_selected}"
    
    # ✅ Queries for Single Shift
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
        SELECT "Machine", "batch number", a."Product" AS "Product", SUM("quantity") AS "Produced Quantity"
        FROM archive a
        WHERE "Activity" = 'Production' AND "Date" = :date AND "Day/Night/plan" = :shift
        GROUP BY "Machine", "batch number", a."Product"
        ORDER BY "Machine", "batch number";
    """
    
elif report_type == "Date Range Report":
    start_date = st.date_input("📅 Start Date")
    end_date = st.date_input("📅 End Date")
    params = {"start_date": start_date, "end_date": end_date}
    file_suffix = f"{start_date}_to_{end_date}"

    # ✅ Queries for Date Range
    query_av = """
        SELECT "machine", "Availability", "Av Efficiency", "OEE"
        FROM av
        WHERE "date" BETWEEN :start_date AND :end_date
    """
    query_archive = """
        SELECT "Machine", "Activity", SUM("time") as "Total_Time", AVG("efficiency") as "Avg_Efficiency"
        FROM archive
        WHERE "Date" BETWEEN :start_date AND :end_date
        GROUP BY "Machine", "Activity"
    """
    query_production = """
        SELECT "Machine", "batch number", a."Product" AS "Product", SUM("quantity") AS "Produced Quantity"
        FROM archive a
        WHERE "Activity" = 'Production' AND "Date" BETWEEN :start_date AND :end_date
        GROUP BY "Machine", "batch number", a."Product"
        ORDER BY "Machine", "batch number";
    """

# ✅ Fetch Data
df_av = get_data(query_av, params)
df_archive = get_data(query_archive, params)
df_production = get_data(query_production, params)

# ✅ Generate Graph
if not df_av.empty:
    st.subheader("📈 Machine Efficiency, Availability & OEE")
    fig = px.bar(df_av, x="machine", y=["Availability", "Av Efficiency", "OEE"], 
                 barmode="group", title="Performance Metrics per Machine",
                 color_discrete_map={"Availability": "#1f77b4", "Av Efficiency": "#ff7f0e", "OEE": "#2ca02c"})
    st.plotly_chart(fig)
else:
    st.warning("⚠️ No AV data available for the selected filters.")

# ✅ Display Tables
st.subheader("📋 Machine Activity Summary")
st.dataframe(df_archive)

st.subheader("🏭 Production Summary per Machine")
st.dataframe(df_production)

# ✅ Function to Create Full Page as HTML
def generate_full_html():
    fig_html = fig.to_html(full_html=False) if not df_av.empty else ""

    return f"""
    <html>
    <head>
        <title>Machine Performance Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .graph-container {{ text-align: center; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>📊 Machine Performance Report</h1>
        <div class="graph-container">{fig_html}</div>
        <h2>📋 Machine Activity Summary</h2>
        {df_archive.to_html(index=False)}
        <h2>🏭 Production Summary</h2>
        {df_production.to_html(index=False)}
        <h2>📈 AV Data</h2>
        {df_av.to_html(index=False)}
    </body>
    </html>
    """

html_bytes = generate_full_html().encode("utf-8")
html_file = f"Report_{file_suffix}.html"

# ✅ HTML Download Button
st.download_button(label="📥 Download Full Page as HTML", 
                   data=html_bytes, 
                   file_name=html_file, 
                   mime="text/html")

# ✅ PDF Download Button
if st.button("📥 Download Full Report as PDF"):
    pdf_report = create_pdf(df_av, df_archive, df_production, fig)
    pdf_file = f"Report_{file_suffix}.pdf"
    
    st.download_button(label="📥 Click here to download", 
                       data=pdf_report, 
                       file_name=pdf_file, 
                       mime="application/pdf")
