import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import text
from db import get_sqlalchemy_engine
from auth import check_authentication, check_access
from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import plotly.io as pio  # ✅ Fix for write_image function
from reportlab.lib.pagesizes import letter
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
    c = canvas.Canvas(buffer, pagesize=letter)  # ✅ Changed to portrait (letter)

    # ✅ Set margins and page dimensions
    margin_x = 40
    margin_y = 40
    width, height = letter

    # ✅ Set PDF Title
    c.setTitle("Machine Performance Report")

    # ✅ Add a title with margins
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_x, height - margin_y, "📊 Machine Performance Report")

    # ✅ Force Plotly to use colored export
    fig.update_layout(
        template="plotly_white",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
    )

    # ✅ Force SVG to preserve colors
    pio.kaleido.scope.default_format = "svg"

    # ✅ Save the figure as PNG with high resolution
    img_buf = io.BytesIO()
    pio.write_image(fig, img_buf, format="png", scale=3)
    img_buf.seek(0)

    # ✅ Embed image in PDF (adjusted for portrait)
    img = ImageReader(img_buf)
    c.drawImage(img, margin_x, height - 300, width=500, height=200)

    # ✅ Function to add tables with proper spacing & text wrapping
    def add_table(c, title, df, y_start):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin_x, y_start, title)
        c.setFont("Helvetica", 10)

        df = df.fillna("N/A").round(2)  # Replace NaN with "N/A"

        if df.empty:
            c.drawString(margin_x, y_start - 20, "No data available")
        else:
            y = y_start - 20
            col_width = 110  # ✅ Wider column width for portrait mode

            # ✅ Add headers with spacing
            for col in df.columns:
                c.drawString(margin_x + df.columns.get_loc(col) * col_width, y, col)
            y -= 15

            # ✅ Add row data with better alignment & text wrapping
            for _, row in df.iterrows():
                x = margin_x
                for item in row:
                    wrapped_text = "\n".join(wrap(str(item), width=12))  # ✅ Wrap long text
                    c.drawString(x, y, wrapped_text)
                    x += col_width
                y -= 15

    # ✅ Add tables with proper spacing (adjusted for portrait mode)
    add_table(c, "📋 Machine Activity Summary", df_archive, height - 350)
    add_table(c, "🏭 Production Summary", df_production, height - 480)
    add_table(c, "📈 AV Data", df_av, height - 600)

    # ✅ Save PDF
    c.save()
    buffer.seek(0)
    return buffer# Streamlit UI
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
