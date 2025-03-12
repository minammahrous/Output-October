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
check_access(["user", "power user", "admin", "report"])  # ✅ Enforce role-based access

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

# ✅ Updated Query: Fetch Production Data with `Product`
query_production = """
    SELECT 
        "Machine", 
        "batch number",  
        a."Product" AS "Product",  
        SUM("quantity") AS "Produced Quantity"
    FROM archive a
    WHERE "Activity" = 'Production' AND "Date" = :date AND "Day/Night/plan" = :shift
    GROUP BY "Machine", "batch number", a."Product"
    ORDER BY "Machine", "batch number";
"""

# ✅ Function to Create PDF Report (No Borders)
def create_pdf(df_av, df_archive, df_production, fig):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)  # ✅ Portrait mode

    # ✅ Set PDF Title
    c.setTitle("Machine Performance Report")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "📊 Machine Performance Report")

    # ✅ Convert Plotly graph to high-quality PNG
    img_buf = io.BytesIO()
    pio.write_image(fig, img_buf, format="png", scale=3)
    img_buf.seek(0)

    # ✅ Embed the colored graph in the PDF
    img = ImageReader(img_buf)
    c.drawImage(img, 50, 500, width=500, height=200)  # Adjusted for portrait mode

    # ✅ Add tables
    add_table(c, "📋 Machine Activity Summary", df_archive, 450)
    add_table(c, "🏭 Production Summary", df_production, 300)  # ✅ Includes `Product`
    add_table(c, "📈 AV Data", df_av, 150)

    # ✅ Save PDF
    c.save()
    buffer.seek(0)  # ✅ Ensure buffer is at the start

    return buffer.getvalue()  # ✅ Convert buffer to binary format

# ✅ Function to Add Tables (Without Borders)
def add_table(c, title, df, y_start):
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_start, title)
    c.setFont("Helvetica", 10)

    df = df.fillna("N/A").applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)

    if df.empty:
        c.drawString(50, y_start - 20, "No data available")
    else:
        y = y_start - 20
        col_widths = [100, 120, 150, 120, 100]  # ✅ Increased column widths for better readability
        row_height = 25  # ✅ Increased row height for spacing
        headers = list(df.columns)

        # ✅ Add headers
        for i, col in enumerate(headers):
            c.drawString(50 + i * 120, y, col)

        y -= row_height

        # ✅ Draw row data with proper alignment
        for _, row in df.iterrows():
            for i, (col_name, item) in enumerate(zip(headers, row)):
                wrapped_text = str(item)

                if col_name == "Product":  # ✅ Wrap Product names correctly
                    wrapped_lines = wrap(str(item), width=25)  
                    for line in wrapped_lines:
                        c.drawString(50 + i * 120, y, line)
                        y -= 12  
                    continue  

                c.drawString(50 + i * 120, y, wrapped_text)  

            y -= row_height

# ✅ Streamlit UI
st.title("📊 Machine Performance Dashboard")

# ✅ User Inputs
date_selected = st.date_input("📅 Select Date")
shift_selected = st.selectbox("🕒 Select Shift Type", ["Day", "Night", "Plan"])

# ✅ Fetch Data
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

df_av = get_data(query_av, {"date": date_selected, "shift": shift_selected})
df_archive = get_data(query_archive, {"date": date_selected, "shift": shift_selected})
df_production = get_data(query_production, {"date": date_selected, "shift": shift_selected})  # ✅ Includes Product

# ✅ Visualize AV Data
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

# ✅ PDF Download Button (Uses Shift Type + Date for File Name)
if st.button("📥 Download Full Report as PDF"):
    pdf_report = create_pdf(df_av, df_archive, df_production, fig)

    # ✅ Generate dynamic filename (format: ShiftType_YYYY-MM-DD.pdf)
    file_name = f"{shift_selected}_{date_selected}.pdf"

    st.download_button(label="📥 Click here to download", 
                       data=pdf_report, 
                       file_name=file_name,  # ✅ Uses dynamic filename
                       mime="application/pdf")
