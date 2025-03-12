import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.sql import text
from db import get_sqlalchemy_engine
from auth import check_authentication, check_access
from io import BytesIO
from fpdf import FPDF
import numpy as np
import pandas as pd
import plotly.io as pio
from PIL import Image
import io


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

# Data Processing: Summary Table
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
    
    summary = df.groupby(["machine", "activity", "batch_number"]).agg(
        quantity=("quantity", "sum"),
        time=("time", "sum"),
        total_batch_quantity=("total_batch_quantity", "max")
    ).reset_index()
    
    return summary

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
    st.subheader("📊 Summary Report")
    st.dataframe(summary_df)

# Restore Graph for Machine Performance
if not st.session_state.df_av.empty:
    st.subheader("📈 Machine Performance Metrics")
    fig = px.bar(st.session_state.df_av, x="machine", y=["availability", "av_efficiency", "oee"],
                 barmode="group", title="Machine Performance", text_auto=True)

    for trace in fig.data:
        trace.text = [f"{y:.2%}" for y in trace.y]

    

def save_summary_graph(summary_df, fig):
    """Combine summary table and graph into a single image."""
    fig_img = io.BytesIO(fig.to_image(format="png"))  # Convert Plotly graph to image
    
    # Convert summary table to an image using Matplotlib
    fig_table, ax = plt.subplots(figsize=(10, len(summary_df) * 0.5 + 1))
    ax.axis('tight')
    ax.axis('off')
    table_data = [summary_df.columns.tolist()] + summary_df.values.tolist()
    table = ax.table(cellText=table_data, colLabels=None, cellLoc='center', loc='center')

    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.auto_set_column_width([i for i in range(len(summary_df.columns))])  # Adjust column width

    table_img = io.BytesIO()
    plt.savefig(table_img, format="png", bbox_inches="tight", dpi=300)
    plt.close(fig_table)

    # Open both images and combine them vertically
    summary_image = Image.open(table_img)
    graph_image = Image.open(fig_img)

    total_width = max(summary_image.width, graph_image.width)
    total_height = summary_image.height + graph_image.height

    combined_image = Image.new("RGB", (total_width, total_height), (255, 255, 255))
    combined_image.paste(summary_image, (0, 0))
    combined_image.paste(graph_image, (0, summary_image.height))

    final_img = io.BytesIO()
    combined_image.save(final_img, format="PNG")
    final_img.seek(0)

    return final_img

# Add download button for the combined image
if not summary_df.empty:
    summary_graph_img = save_summary_graph(summary_df, fig)
    st.download_button(
        label="📥 Download Summary & Graph as PNG",
        data=summary_graph_img,
        file_name="summary_and_graph.png",
        mime="image/png"
    )

