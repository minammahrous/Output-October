import streamlit as st
import datetime
import pandas as pd
import psycopg2
import csv
import os

# Load database credentials
db_params = st.secrets["postgres"]

def get_connection():
    return psycopg2.connect(
        dbname=db_params["neondb"],
        user=db_params["neondb_owner"],
        password=db_params["npg_iP24WhuZvaws"],
        host=db_params["ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech"],
        port=db_params["5432"]
    )

st.title("Shift Output Report")

# Initialize session state
if "submitted_archive_df" not in st.session_state:
    st.session_state.submitted_archive_df = pd.DataFrame()
if "submitted_av_df" not in st.session_state:
    st.session_state.submitted_av_df = pd.DataFrame()
if "modify_mode" not in st.session_state:
    st.session_state.modify_mode = False

# Load machine and product lists
machine_list, product_list = [], []
for filename, target_list in zip(["machines.csv", "products.csv"], [machine_list, product_list]):
    try:
        with open(filename, "r") as file:
            target_list.extend(row[0] for row in csv.reader(file))
    except FileNotFoundError:
        st.error(f"{filename} file not found. Please create the file.")
    except Exception as e:
        st.error(f"Error reading {filename}: {e}")

# Ensure product list is not empty
if not product_list:
    st.error("Product list is empty. Please check products.csv.")
else:
    try:
        shifts_df = pd.read_csv("shifts.csv")
        shift_durations = shifts_df["code"].tolist()
    except FileNotFoundError:
        st.error("shifts.csv file not found.")
        shift_durations = []

    selected_machine = st.selectbox("Select Machine", machine_list)
    date = st.date_input("Date", datetime.datetime.now().date())
    shift_type = st.selectbox("Shift Type", ["Day", "Night", "Plan"])
    shift_duration = st.selectbox("Shift Duration", shift_durations)
    
    # Downtime inputs
    downtime_data = {}
    downtime_types = ["Maintenance DT", "Production DT", "Material DT", "Utility DT", "QC DT", "Cleaning DT", "QA DT", "Changeover DT"]
    for dt_type in downtime_types:
        downtime_data[dt_type] = st.number_input(dt_type, min_value=0.0, step=0.1, format="%.1f")
        if downtime_data[dt_type] > 0:
            downtime_data[dt_type + "_comment"] = st.text_area(f"Comment for {dt_type}")
        else:
            downtime_data[dt_type + "_comment"] = ""

    # Product batch entry
    selected_product = st.selectbox("Select Product", product_list)
    if "product_batches" not in st.session_state:
        st.session_state.product_batches = {}
    if selected_product not in st.session_state.product_batches:
        st.session_state.product_batches[selected_product] = []
    
    with st.form("batch_entry_form"):
        batch = st.text_input("Batch Number")
        quantity = st.number_input("Production Quantity", min_value=0.0, step=0.1)
        time_consumed = st.number_input("Time Consumed (hours)", min_value=0.0, step=0.1)
        if st.form_submit_button("Add Batch"):
            if len(st.session_state.product_batches[selected_product]) < 5:
                st.session_state.product_batches[selected_product].append({
                    "batch": batch, "quantity": quantity, "time_consumed": time_consumed
                })
            else:
                st.error("Max 5 batches per product.")

    if st.button("Submit Report"):
        archive_data = [
            {
                "Date": date, "Machine": selected_machine, "Day/Night/plan": shift_type,
                "Activity": dt_type, "time": downtime_data[dt_type], "Product": "",
                "batch number": "", "quantity": "", "commnets": downtime_data[dt_type + "_comment"],
                "rate": "", "standard rate": "", "efficiency": ""
            }
            for dt_type in downtime_types if downtime_data[dt_type] > 0
        ]
        
        try:
            rates_df = pd.read_csv("rates.csv")
            for batch in st.session_state.product_batches[selected_product]:
                rate = batch["quantity"] / batch["time_consumed"]
                standard_rate = rates_df.loc[(rates_df['Product'] == selected_product) & (rates_df['Machine'] == selected_machine), 'Rate'].iloc[0]
                efficiency = rate / standard_rate if standard_rate != 0 else 0
                archive_data.append({
                    "Date": date, "Machine": selected_machine, "Day/Night/plan": shift_type,
                    "Activity": "Production", "time": batch["time_consumed"], "Product": selected_product,
                    "batch number": batch["batch"], "quantity": batch["quantity"], "commnets": "",
                    "rate": rate, "standard rate": standard_rate, "efficiency": efficiency
                })
        except FileNotFoundError:
            st.error("rates.csv was not found")
        
        archive_df = pd.DataFrame(archive_data)
        st.session_state.submitted_archive_df = archive_df
        
        # Save to Neon PostgreSQL
        try:
            conn = get_connection()
            cursor = conn.cursor()
            for _, row in archive_df.iterrows():
                cursor.execute(
                    """
                    INSERT INTO archive (date, machine, shift_type, activity, time, product, batch_number, quantity, comments, rate, standard_rate, efficiency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, tuple(row)
                )
            conn.commit()
            st.success("Data saved to Neon PostgreSQL successfully!")
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving data: {e}")
        finally:
            cursor.close()
            conn.close()
