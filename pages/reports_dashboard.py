import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import text
from db import get_sqlalchemy_engine
from auth import check_authentication, check_access
from io import BytesIO
from fpdf import FPDF
import numpy as np

# Hide Streamlit's menu and "Manage app" button
st.markdown("""
    <style>
        [data-testid="stToolbar"] {visibility: hidden !important;}
        [data-testid="manage-app-button"] {display: none !important;}
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}
    </style>
""", unsafe_allow_html=True)

# Authenticate user
check_authentication()
check_access(["user", "power user", "admin", "report"])

# Get database engine
engine = get_sqlalchemy_engine()

def get_data(query, params=None):
    """Fetch data from Neon PostgreSQL while preserving NULL values."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df.replace({None: np.nan})  # Ensure NULLs stay as NaN
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return pd.DataFrame()

st.title("📊 Machine Performance Dashboard")

# Initialize session state for reports
if "df_av" not in st.session_state:
    st.session_state.df_av = None
if "df_archive" not in st.session_state:
    st.session_state.df_archive = None
if "report_type" not in st.session_state:
    st.session_state.report_type = None
if "report_name" not in st.session_state:
    st.session_state.report_name = "report"

# Select Shift Report
date_selected = st.date_input("📅 Select Date")
shift_selected = st.selectbox("🕒 Select Shift Type", ["Day", "Night", "Plan"])
if st.button("Run Shift Report"):
    st.session_state.df_av = get_data("SELECT * FROM av WHERE date = :date AND shift = :shift", {"date": date_selected, "shift": shift_selected})
    st.session_state.df_archive = get_data('SELECT * FROM archive WHERE "Date" = :date AND "Day/Night/plan" = :shift', {"date": date_selected, "shift": shift_selected})
    st.session_state.report_type = "shift"
    st.session_state.report_name = f"shift_report_{date_selected}"

# Custom Date Range Report
st.subheader("📅 Select Date Range for Custom Report")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
if st.button("Run Custom Report"):
    st.session_state.df_av = get_data("SELECT * FROM av WHERE date BETWEEN :start_date AND :end_date", {"start_date": start_date, "end_date": end_date})
    st.session_state.df_archive = get_data('SELECT * FROM archive WHERE "Date" BETWEEN :start_date AND :end_date', {"start_date": start_date, "end_date": end_date})
    st.session_state.report_type = "custom"
    st.session_state.report_name = f"custom_report_{start_date}_to_{end_date}"

# Data Processing: Summarize by Machine
def process_summary(df):
    if df is None or df.empty:
        return pd.DataFrame()
    summary = df.groupby(["Machine", "Activity", "batch number"]).agg(
        Quantity=("quantity", "sum"),
        Time=("time", "sum"),
        Total_Quantity=("quantity", "sum")
    ).reset_index()
    return summary.replace({None: np.nan})

summary_df = process_summary(st.session_state.df_archive)
downtime_summary = st.session_state.df_archive.groupby("Activity")[["time", "comments"]].agg({"time": "sum", "comments": lambda x: ", ".join(x.dropna().astype(str).unique())}).reset_index()

def generate_charts(df):
    if df is None or df.empty:
        return
    available_columns = [col for col in ["Availability", "Av Efficiency", "OEE"] if col in df.columns]
    if available_columns:
        avg_metrics = df.groupby("Machine")[available_columns].mean().reset_index()
        fig = px.bar(avg_metrics, x="Machine", y=available_columns, barmode="group", title="Machine Performance Metrics")
        st.plotly_chart(fig)
    else:
        st.warning("⚠️ Required columns for metrics visualization are missing.")
    
st.write("Columns in df_av:", st.session_state.df_av.columns)
st.write(st.session_state.df_av.head())
generate_charts(st.session_state.df_av)

# Export to PDF
def generate_pdf(summary_df, downtime_summary):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Machine Performance Report", ln=True, align='C')
    pdf.ln(10)
    
    def add_table(pdf, df, title):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("Arial", "", 10)
        
        if df.empty:
            pdf.cell(0, 10, "No data available", ln=True)
            pdf.ln(5)
            return
        
        df = df.fillna("")  # Keep NaN values as empty
        columns = df.columns.tolist()
        column_width = max(190 // len(columns), 20)
        
        pdf.set_font("Arial", "B", 10)
        for col in columns:
            pdf.cell(column_width, 10, col[:15], border=1, align='C')
        pdf.ln()
        
        pdf.set_font("Arial", "", 8)
        for _, row in df.iterrows():
            for col in columns:
                value = row[col]
                if isinstance(value, (int, float)):
                    value = f"{value:.2f}"  # Limit to 2 decimal places
                pdf.cell(column_width, 10, str(value)[:15], border=1, align='C')
            pdf.ln()
        pdf.ln(5)
    
    add_table(pdf, summary_df, "Machine Summary")
    add_table(pdf, downtime_summary, "Downtime Summary")
    
    pdf_output = BytesIO()
    pdf.output(pdf_output, dest='S').encode('latin1')
    pdf_output.seek(0)
    return pdf_output

if st.button("Download PDF Report"):
    if not summary_df.empty:
        pdf_file = generate_pdf(summary_df, downtime_summary)
        st.download_button("Download PDF", pdf_file, f"{st.session_state.report_name}.pdf", "application/pdf")
    else:
        st.error("❌ No data available for the PDF report.")
