import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import text
from db import get_sqlalchemy_engine
from auth import check_authentication, check_access
from fpdf import FPDF
import matplotlib.pyplot as plt
import io

from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
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

# Function to generate PDF with Unicode support
def create_pdf(df_av, df_archive, df_production, fig):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, 550, "📊 Machine Performance Report")

    # Convert Plotly figure to image
    img_buf = io.BytesIO()
    fig.write_image(img_buf, format="png")
    img_buf.seek(0)
    img = ImageReader(img_buf)
    c.drawImage(img, 30, 300, width=500, height=200)

    # Function to add a table
    def add_table(c, title, df, y_start):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y_start, title)
        c.setFont("Helvetica", 10)

        if df.empty:
            c.drawString(30, y_start - 20, "No data available")
        else:
            y = y_start - 20
            for col in df.columns:
                c.drawString(30, y, col)
                y -= 15
            y -= 10
            for _, row in df.iterrows():
                x = 30
                for item in row:
                    c.drawString(x, y, str(item))
                    x += 100
                y -= 15

    
   

# Streamlit UI
st.title("📊 Machine Performance Dashboard")

# Sample Data (Replace with actual database data)
df_av = pd.DataFrame({"machine": ["A", "B"], "Availability": [90, 85], "OEE": [80, 75]})
df_archive = pd.DataFrame({"Machine": ["A", "B"], "Activity": ["Run", "Stop"], "Total_Time": [120, 45]})
df_production = pd.DataFrame({"Machine": ["A"], "batch number": ["B001"], "Produced Quantity": [1000]})

# Generate Graph
fig = px.bar(df_av, x="machine", y=["Availability", "OEE"], barmode='group', title="Performance Metrics")
# Add tables
add_table(c, "📋 Machine Activity Summary", df_archive, 250)
add_table(c, "🏭 Production Summary", df_production, 150)
add_table(c, "📈 AV Data", df_av, 50)

# PDF Download Button
if st.button("📥 Download Full Report as PDF"):
       # Save PDF
    c.save()
    buffer.seek(0)
return buffer



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

def create_pdf(df_av, df_archive, df_production, fig):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "📊 Machine Performance Report", ln=True, align="C")
    pdf.ln(10)
    pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", "", 16)
    pdf.cell(200, 10, "📊 Machine Performance Report", ln=True, align="C")


    # Add the graph as an image
    img_buf = io.BytesIO()
    fig.write_image(img_buf, format="png")
    img_buf.seek(0)
    pdf.image(img_buf, x=10, y=pdf.get_y(), w=180)

    pdf.ln(90)  # Move below the graph

    # Function to add a table
    def add_table(pdf, title, df):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(200, 10, title, ln=True)
        pdf.set_font("Arial", "", 10)

        if df.empty:
            pdf.cell(200, 10, "No data available", ln=True)
        else:
            col_widths = [40] * len(df.columns)  # Adjust column width
            for col in df.columns:
                pdf.cell(col_widths[0], 10, col, border=1, align="C")
            pdf.ln()

            for _, row in df.iterrows():
                for item in row:
                    pdf.cell(col_widths[0], 10, str(item), border=1, align="C")
                pdf.ln()
        pdf.ln(5)

    # Add tables
    add_table(pdf, "📋 Machine Activity Summary", df_archive)
    add_table(pdf, "🏭 Production Summary", df_production)
    add_table(pdf, "📈 AV Data", df_av)

    # Save the PDF in memory
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# Create the PDF button
if st.button("📥 Download Full Report as PDF"):
    pdf_report = create_pdf(df_av, df_archive, df_production, fig)
    st.download_button(label="📥 Click here to download",
                       data=pdf_report,
                       file_name=f"Machine_Performance_Report_{date_selected}.pdf",
                       mime="application/pdf")
