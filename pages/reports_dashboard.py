import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import io
from sqlalchemy.sql import text
from db import get_sqlalchemy_engine
from auth import check_authentication, check_access
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

# Ensure session state variables are initialized
if "df_av" not in st.session_state:
    st.session_state.df_av = pd.DataFrame()

if "df_archive" not in st.session_state:
    st.session_state.df_archive = pd.DataFrame()

# Restore Graph for Machine Performance
if not st.session_state.df_av.empty:
    st.subheader("📈 Machine Performance Metrics")
    fig = px.bar(st.session_state.df_av, x="machine", y=["availability", "av_efficiency", "oee"],
                 barmode="group", title="Machine Performance", text_auto=True)

    for trace in fig.data:
        trace.text = [f"{y:.2%}" for y in trace.y]

    st.plotly_chart(fig)

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
if not st.session_state.df_archive.empty:
    summary_graph_img = save_summary_graph(st.session_state.df_archive, fig)
    st.download_button(
        label="📥 Download Summary & Graph as PNG",
        data=summary_graph_img,
        file_name="summary_and_graph.png",
        mime="image/png"
    )
