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
    """Fetch data from Neon PostgreSQL while preserving NULL values and standardizing column names."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        
        df = df.replace({None: np.nan})  # Ensure NULLs stay as NaN
        
        # Standardize column names (lowercase and replace spaces with underscores)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

        return df
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
    st.session_state.df_archive = get_data("SELECT * FROM archive WHERE \"Date\" = :date AND \"Day/Night/plan\" = :shift", {"date": date_selected, "shift": shift_selected})
    st.session_state.report_type = "shift"
    st.session_state.report_name = f"shift_report_{date_selected}"

# Custom Date Range Report
st.subheader("📅 Select Date Range for Custom Report")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
if st.button("Run Custom Report"):
    st.session_state.df_av = get_data("SELECT * FROM av WHERE date BETWEEN :start_date AND :end_date", {"start_date": start_date, "end_date": end_date})
    st.session_state.df_archive = get_data("SELECT * FROM archive WHERE \"Date\" BETWEEN :start_date AND :end_date", {"start_date": start_date, "end_date": end_date})
    st.session_state.report_type = "custom"
    st.session_state.report_name = f"custom_report_{start_date}_to_{end_date}"

# Data Processing: Pivot Summary by Machine
def process_summary(df):
    if df is None or df.empty:
        return pd.DataFrame()

    required_columns = {"machine", "activity", "batch_number", "quantity", "time"}
    missing_columns = required_columns - set(df.columns)
    
    if missing_columns:
        st.error(f"❌ Required columns are missing: {', '.join(missing_columns)}")
        return pd.DataFrame()
    
    # Calculate total quantity for the same batch on the same machine
    df["total_batch_quantity"] = df.groupby(["machine", "batch_number"])["quantity"].transform("sum")
    
    summary = df.pivot_table(index=["machine", "activity"], columns="batch_number", values=["quantity", "time", "total_batch_quantity"], aggfunc="sum").fillna(0)
    return summary.reset_index()

summary_df = process_summary(st.session_state.df_archive)
if "activity" in st.session_state.df_archive.columns:
    downtime_summary = st.session_state.df_archive.groupby("activity")[["time", "comments"]].agg(
        {"time": "sum", "comments": lambda x: ", ".join(x.dropna().astype(str).unique())}
    ).reset_index()
else:
    downtime_summary = pd.DataFrame()
    st.warning("⚠️ 'activity' column is missing in the archive data. Please check the source.")

# Display Summary Table
if not summary_df.empty:
    st.subheader("📊 Summary Report (Pivot View)")
    st.dataframe(summary_df)

def generate_pdf(summary_df, downtime_summary):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Machine Performance Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Summary Table", ln=True)
    pdf.set_font("Arial", "", 10)
    
    for i, row in summary_df.iterrows():
        pdf.cell(0, 10, str(row.tolist()), ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Downtime Summary", ln=True)
    pdf.set_font("Arial", "", 10)
    
    for i, row in downtime_summary.iterrows():
        pdf.cell(0, 10, str(row.tolist()), ln=True)
    pdf.ln(5)
    
    pdf_output = BytesIO()
    pdf.output(pdf_output, dest='S')
    pdf_output.seek(0)
    return pdf_output

if st.button("Download PDF Report"):
    if not summary_df.empty:
        pdf_file = generate_pdf(summary_df, downtime_summary)
        st.download_button("Download PDF", pdf_file, f"{st.session_state.report_name}.pdf", "application/pdf")
    else:
        st.error("❌ No data available for the PDF report.")
