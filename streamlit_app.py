import streamlit as st
import pandas as pd
import psycopg2
import csv
from datetime import datetime

# Function to get connection to Neon PostgreSQL
def get_connection():
    return psycopg2.connect(
        dbname="your_db_name",
        user="your_db_user",
        password="your_db_password",
        host="your_db_host",
        port="your_db_port"
    )

# Load machine list
try:
    machine_list = pd.read_csv("machines.csv", header=None).squeeze().tolist()
except FileNotFoundError:
    st.error("machines.csv file not found. Please create the file.")
    machine_list = []

# Load product list
try:
    product_list = pd.read_csv("products.csv", header=None).squeeze().tolist()
except FileNotFoundError:
    st.error("products.csv file not found. Please create the file.")
    product_list = []

# Streamlit UI
st.title("Production Data Entry")

# Select Machine
date = st.date_input("Select Date", datetime.today())
machine = st.selectbox("Select Machine", machine_list)
shift_type = st.selectbox("Select Shift", ["Day", "Night", "Planned Downtime"])

# Input Production Data
activity = st.text_input("Activity")
time = st.number_input("Time (hours)", min_value=0.0, step=0.1)
product = st.selectbox("Select Product", product_list)
batch_number = st.text_input("Batch Number")
quantity = st.number_input("Quantity Produced", min_value=0, step=1)
comments = st.text_area("Comments")
rate = st.number_input("Rate", min_value=0.0, step=0.1)
standard_rate = st.number_input("Standard Rate", min_value=0.0, step=0.1)
efficiency = st.number_input("Efficiency (%)", min_value=0.0, max_value=100.0, step=0.1)

# Handle downtime input
downtime_types = ["Mechanical", "Electrical", "Changeover", "Quality", "Cleaning"]
downtime_data = {}
for dt_type in downtime_types:
    downtime_data[dt_type] = st.number_input(f"{dt_type} Downtime (hours)", min_value=0.0, step=0.1)
    downtime_data[dt_type + "_comment"] = st.text_area(f"Comment for {dt_type}") if downtime_data[dt_type] > 0 else ""

# Store input in session state if not exists
if "batch_data" not in st.session_state:
    st.session_state.batch_data = []

# Add entry to batch
if st.button("Add to Batch"):
    new_entry = {
        "Date": date,
        "Machine": machine,
        "Shift": shift_type,
        "Activity": activity,
        "Time": time,
        "Product": product,
        "Batch Number": batch_number,
        "Quantity": quantity,
        "Comments": comments,
        "Rate": rate,
        "Standard Rate": standard_rate,
        "Efficiency": efficiency,
        **downtime_data
    }
    st.session_state.batch_data.append(new_entry)
    st.success("Entry added to batch!")

# Display batch data
if st.session_state.batch_data:
    st.dataframe(pd.DataFrame(st.session_state.batch_data))

# Submit to Database
if st.button("Submit to Database"):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        for entry in st.session_state.batch_data:
            cursor.execute(
                """
                INSERT INTO archive (date, machine, shift_type, activity, time, product, batch_number, quantity, comments, rate, standard_rate, efficiency)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry["Date"], entry["Machine"], entry["Shift"], entry["Activity"], entry["Time"],
                    entry["Product"], entry["Batch Number"], entry["Quantity"], entry["Comments"],
                    entry["Rate"], entry["Standard Rate"], entry["Efficiency"]
                )
            )
        conn.commit()
        st.success("Data saved successfully!")
        st.session_state.batch_data = []
    except Exception as e:
        conn.rollback()
        st.error(f"Error saving data: {e}")
    finally:
        cursor.close()
        conn.close()

# Modify Data Mode
if st.button("Modify Existing Data"):
    st.session_state.modify_mode = True

if "modify_mode" in st.session_state and st.session_state.modify_mode:
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM archive", conn)
    conn.close()
    modified_df = st.data_editor(df, num_rows="dynamic")

    if st.button("Confirm Modifications and Save"):
        try:
            conn = get_connection()
            cursor = conn.cursor()

            for _, row in modified_df.iterrows():
                cursor.execute(
                    """
                    UPDATE archive
                    SET time = %s, product = %s, batch_number = %s, quantity = %s, comments = %s, rate = %s, standard_rate = %s, efficiency = %s
                    WHERE date = %s AND machine = %s AND shift_type = %s AND activity = %s
                    """,
                    (
                        row["Time"], row["Product"], row["Batch Number"], row["Quantity"], row["Comments"],
                        row["Rate"], row["Standard Rate"], row["Efficiency"],
                        row["Date"], row["Machine"], row["Shift"], row["Activity"]
                    )
                )
            conn.commit()
            st.success("Modifications saved successfully.")
            st.session_state.modify_mode = False
        except Exception as e:
            conn.rollback()
            st.error(f"Error updating data: {e}")
        finally:
            cursor.close()
            conn.close()
