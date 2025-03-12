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
    
    # Set PDF title
    c.setTitle("Machine Performance Report")

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, 550, "📊 Machine Performance Report")

    # ✅ Convert Plotly figure to an image
    img_buf = io.BytesIO()
    pio.write_image(fig, img_buf, format="png")  # ✅ Uses Kaleido
    img_buf.seek(0)
    img = ImageReader(img_buf)
    c.drawImage(img, 30, 300, width=500, height=200)

    # ✅ Function to add tables with improved spacing
    def add_table(c, title, df, y_start):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y_start, title)
        c.setFont("Helvetica", 10)

        df = df.fillna("N/A").round(2)  # ✅ Replace NaN with "N/A" and round numbers

        if df.empty:
            c.drawString(30, y_start - 20, "No data available")
        else:
            y = y_start - 20
            col_width = 100  # Adjust column width

            # ✅ Add headers
            for col in df.columns:
                c.drawString(30 + df.columns.get_loc(col) * col_width, y, col)
            y -= 15

            # ✅ Add row data with spacing
            for _, row in df.iterrows():
                x = 30
                for item in row:
                    c.drawString(x, y, str(item))
                    x += col_width
                y -= 15

    # ✅ Add tables
    add_table(c, "📋 Machine Activity Summary", df_archive, 250)
    add_table(c, "🏭 Production Summary", df_production, 150)
    add_table(c, "📈 AV Data", df_av, 50)

    # ✅ Save PDF
    c.save()
    buffer.seek(0)
    return buffer

# Streamlit UI
st.title("📊 Machine Performance Dashboard")

# Sample Data (Replace with actual database data)
df_av = pd.DataFrame({"machine": ["A", "B"], "Availability": [90, 85], "OEE": [80, 75]})
df_archive = pd.DataFrame({"Machine": ["A", "B"], "Activity": ["Run", "Stop"], "Total_Time": [120, 45]})
df_production = pd.DataFrame({"Machine": ["A"], "batch number": ["B001"], "Produced Quantity": [1000]})

# Generate Graph
fig = px.bar(df_av, x="machine", y=["Availability", "OEE"], barmode='group', title="Performance Metrics")

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

# Generate Graph
fig = px.bar(df_av, x="machine", y=["Availability", "OEE"], barmode='group', title="Performance Metrics")

# PDF Download Button
if st.button("📥 Download Full Report as PDF"):
    pdf_report = create_pdf(df_av, df_archive, df_production, fig)
    st.download_button(label="📥 Click here to download",
                       data=pdf_report,
                       file_name="Machine_Performance_Report.pdf",
                       mime="application/pdf")
