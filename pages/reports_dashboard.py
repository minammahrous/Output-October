import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import text
from db import get_sqlalchemy_engine
from auth import check_authentication, check_access
from io import BytesIO
from fpdf import FPDF

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
    """Fetch data from Neon PostgreSQL."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params)
        return df
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        return pd.DataFrame()

st.title("📊 Machine Performance Dashboard")

# Select Shift Report
date_selected = st.date_input("📅 Select Date")
shift_selected = st.selectbox("🕒 Select Shift Type", ["Day", "Night", "Plan"])
if st.button("Run Shift Report"):
    df_av = get_data("SELECT * FROM av WHERE date = :date AND shift = :shift", {"date": date_selected, "shift": shift_selected})
    df_archive = get_data('SELECT * FROM archive WHERE "Date" = :date AND "Day/Night/plan" = :shift', {"date": date_selected, "shift": shift_selected})
    st.dataframe(df_av)
    st.dataframe(df_archive)

# Custom Date Range Report
st.subheader("📅 Select Date Range for Custom Report")
start_date = st.date_input("Start Date")
end_date = st.date_input("End Date")
if st.button("Run Custom Report"):
    df_av = get_data("SELECT * FROM av WHERE date BETWEEN :start_date AND :end_date", {"start_date": start_date, "end_date": end_date})
    df_archive = get_data('SELECT * FROM archive WHERE "Date" BETWEEN :start_date AND :end_date', {"start_date": start_date, "end_date": end_date})
    st.dataframe(df_av)
    st.dataframe(df_archive)

# Export to PDF
def generate_pdf(df_av, df_archive):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Machine Performance Report", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "AV Data", ln=True)
    pdf.set_font("Arial", "", 10)
    for index, row in df_av.iterrows():
        pdf.cell(0, 10, str(row.to_dict()), ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Archive Data", ln=True)
    pdf.set_font("Arial", "", 10)
    for index, row in df_archive.iterrows():
        pdf.cell(0, 10, str(row.to_dict()), ln=True)
    
    pdf_output = BytesIO()
    pdf.output(pdf_output, 'F')
    pdf_output.seek(0)
    return pdf_output

if st.button("Download PDF Report"):
    pdf_file = generate_pdf(df_av, df_archive)
    st.download_button("Download PDF", pdf_file, "report.pdf", "application/pdf")

# Export to Excel
def generate_excel(df_av, df_archive):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_av.to_excel(writer, sheet_name='AV Data', index=False)
        df_archive.to_excel(writer, sheet_name='Archive Data', index=False)
    output.seek(0)
    return output

if st.button("Download Excel Report"):
    excel_file = generate_excel(df_av, df_archive)
    st.download_button("Download Excel", excel_file, "report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
