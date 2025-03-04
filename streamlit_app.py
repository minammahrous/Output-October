import streamlit as st
import pandas as pd
import datetime
from sqlalchemy import create_engine, text

# Load database credentials from Streamlit secrets
DB_URL = st.secrets["database"]["DB_URL"]
engine = create_engine(DB_URL)

# Function to create database tables if they don't exist
def create_tables():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS reports (
            id SERIAL PRIMARY KEY,
            date DATE,
            machine TEXT,
            shift_type TEXT,
            shift_duration TEXT,
            downtime JSONB,
            product TEXT,
            batch TEXT,
            quantity FLOAT,
            time_consumed FLOAT
        );
        """))
        conn.commit()  # Ensure changes are committed

# Initialize database
create_tables()

# Function to load CSV data
def load_csv(filename):
    try:
        return pd.read_csv(filename)
    except FileNotFoundError:
        st.error(f"Error: {filename} not found!")
        return pd.DataFrame()

# Load CSV files (machines, products, shifts, rates)
machines_df = load_csv("machines.csv")
products_df = load_csv("products.csv")
shifts_df = load_csv("shifts.csv")
rates_df = load_csv("rates.csv")

# Convert CSV data to lists
machine_list = machines_df.iloc[:, 0].tolist() if not machines_df.empty else []
product_list = products_df.iloc[:, 0].tolist() if not products_df.empty else []
shift_durations = shifts_df["code"].tolist() if "code" in shifts_df else []

st.title("Shift Output Report")

# Dropdown selections
selected_machine = st.selectbox("Select Machine", machine_list)
selected_product = st.selectbox("Select Product", product_list)

# Date & Shift selection
now = datetime.datetime.now()
default_date = now.date() if now.hour >= 9 else now.date() - datetime.timedelta(days=1)
date = st.date_input("Date", default_date)
shift_types = ["Day", "Night", "Plan"]
shift_type = st.selectbox("Shift Type", shift_types)
shift_duration = st.selectbox("Shift Duration", shift_durations)

# Downtime Inputs
st.subheader("Downtime (hours)")
downtime_types = ["Maintenance", "Production", "Material", "Utility", "QC", "Cleaning"]
downtime_data = {dt: st.number_input(dt, min_value=0.0, step=0.1) for dt in downtime_types}

# Batch Data Entry
st.subheader("Batch Data")
batch = st.text_input("Batch Number")
quantity = st.number_input("Production Quantity", min_value=0.0, step=0.1)
time_consumed = st.number_input("Time Consumed (hours)", min_value=0.0, step=0.1)

# Submit Data to Database
if st.button("Submit Report"):
    try:
        with engine.connect() as conn:
            conn.execute(text("""
            INSERT INTO reports (date, machine, shift_type, shift_duration, downtime, product, batch, quantity, time_consumed)
            VALUES (:date, :machine, :shift_type, :shift_duration, :downtime, :product, :batch, :quantity, :time_consumed);
            """), {
                "date": date,
                "machine": selected_machine,
                "shift_type": shift_type,
                "shift_duration": shift_duration,
                "downtime": str(downtime_data),
                "product": selected_product,
                "batch": batch,
                "quantity": quantity,
                "time_consumed": time_consumed
            })
        st.success("Report submitted successfully!")
    except Exception as e:
        st.error(f"Error saving data: {e}")

# Display Stored Reports
st.subheader("Previous Reports")
try:
    df = pd.read_sql("SELECT * FROM reports ORDER BY date DESC LIMIT 10", con=engine)
    st.dataframe(df)
except Exception as e:
    st.error(f"Error loading data: {e}")
