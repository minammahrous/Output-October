import streamlit as st

st.title("Welcome to the App")
st.write("Use the sidebar to navigate.")

# Add navigation to pages
st.page_link("pages/shift_output_form.py", label="Shift Output Form")
st.page_link("pages/reports_dashboard.py", label="Reports Dashboard")
