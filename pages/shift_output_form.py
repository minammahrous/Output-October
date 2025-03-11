import streamlit as st
import datetime
import pandas as pd
import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.sql import text  # Import SQL text wrapper
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from db import get_sqlalchemy_engine
from db import get_db_connection
from decimal import Decimal
import numpy as np
# Establish the connection
engine = get_sqlalchemy_engine()
conn = engine.connect()
if not conn:
    st.error("❌ Database connection failed. Please check your credentials.")
    st.stop()

def get_standard_rate(product, machine):
    conn = get_db_connection()  # Make sure to define this function
    cur = conn.cursor()
    
    cur.execute("SELECT standard_rate FROM rates WHERE product = %s AND machine = %s", (product, machine))
    result = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return Decimal(result[0]) if result else Decimal("0")  # Return 0 if no rate is found

# Function to fetch data from PostgreSQL
def fetch_data(query):
    """Fetch data using SQLAlchemy engine."""
    engine = get_sqlalchemy_engine()
    try:
        df = pd.read_sql(query, engine)  # ✅ Use SQLAlchemy engine
        return df["name"].tolist()
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return []

# Function to fetch machine data from PostgreSQL
def fetch_machine_data():
    """Fetch machine names and corresponding qty_uom values."""
    engine = get_sqlalchemy_engine()
    query = "SELECT name, qty_uom FROM machines"
    try:
        df = pd.read_sql(query, engine)
        return df.set_index("name")["qty_uom"].to_dict()
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return {}
# Fetch machine list from database
machine_data = fetch_machine_data()
machine_list = list(machine_data.keys())  # Extract machine names
# Fetch product list from database
product_list = fetch_data("SELECT name FROM products")

# Check if product_list is empty
if not product_list:
    st.error("⚠️ Product list is empty. Please check the database.")
def clean_dataframe(df):
    """
    Cleans the dataframe by:
    1. Converting column names to strings to prevent errors.
    2. Stripping whitespaces from column names.
    3. Converting empty strings in numeric columns to NaN.
    4. Ensuring consistent data types.
    """
    df.columns = df.columns.astype(str).str.strip()  # Ensure all column names are strings
    
    numeric_cols = ["time", "quantity", "rate", "standard rate", "efficiency"]  # Adjust as needed

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert to float, replace invalid values with NaN
    
    return df


st.title("Shift Output Report")

# Initialize session state for submitted data and modify mode
if "submitted_archive_df" not in st.session_state:
    st.session_state.submitted_archive_df = pd.DataFrame()
if "submitted_av_df" not in st.session_state:
    st.session_state.submitted_av_df = pd.DataFrame()
if "modify_mode" not in st.session_state:
    st.session_state.modify_mode = False
if st.button("Restart App"):
    st.markdown(
        """<meta http-equiv="refresh" content="0">""",
        unsafe_allow_html=True,
    )
# Check if product_list is empty
if not product_list:
    st.error("Product list is empty. Please check products.csv.")
else:
    # Read shift types from shifts.csv
    try:
        shifts_df = pd.read_csv("shifts.csv")
        shift_durations = shifts_df["code"].tolist()
        shift_working_hours = shifts_df["working hours"].tolist()
    except FileNotFoundError:
        st.error("shifts.csv file not found. Please create the file.")
        shift_durations = []
        shift_working_hours = []
    except Exception as e:
        st.error(f"An error occurred reading shifts.csv: {e}")
        shift_durations = []
        shift_working_hours = []
# Step 1: User selects Date, Machine, and Shift Type
st.subheader("Step 1: Select Shift Details")
shift_types = ["Day", "Night", "Plan"]
date = st.date_input("Date", None, key="date")  
selected_machine = st.selectbox("Select Machine", [""] + machine_list, index=0, key="machine")
if selected_machine:
    qty_uom = machine_data.get(selected_machine, "Unknown UOM")
    st.info(f"ℹ️ **{selected_machine}**: Production quantity is entered as **{qty_uom}**")

shift_type = st.selectbox("Shift Type", [""] + shift_types, index=0, key="shift_type")
if st.button("Proceed"):
    st.session_state.proceed_clicked = True
    st.rerun()
if st.session_state.get("proceed_clicked", False):
    # Query to check if a record exists in 'av' table
    query = text("""
        SELECT COUNT(*) FROM av 
        WHERE date = :date AND shift = :shift AND machine = :machine
    """)

    conn = get_db_connection()
if not conn:
    st.error("❌ Database connection failed. Please check credentials and try again.")
    st.stop()

cur = conn.cursor()

# ✅ Check if a record already exists
query = """
    SELECT COUNT(*) FROM av WHERE date = %s AND shift = %s AND machine = %s
"""
cur.execute(query, (date, shift_type, selected_machine))
result = cur.fetchone()

if result and result[0] > 0:  # If a record already exists
    st.warning("⚠️ A report for this Date, Shift Type, and Machine already exists. Choose an action.")

col1, col2 = st.columns(2)

if col1.button("🗑️ Delete Existing Data and Proceed"):
    try:
        # ✅ Check for existing records before deleting
        check_query_av = """
            SELECT * FROM av WHERE date = %s AND shift = %s AND machine = %s
        """
        cur.execute(check_query_av, (date, shift_type, selected_machine))
        result_av = cur.fetchall()

        check_query_archive = """
            SELECT * FROM archive WHERE "Date" = %s AND "Machine" = %s AND "Day/Night/plan" = %s
        """
        cur.execute(check_query_archive, (date, selected_machine, shift_type))
        result_archive = cur.fetchall()

        # ✅ Show records before deletion
        if not result_av and not result_archive:
            st.warning("⚠️ No matching records found. Nothing to delete.")
        else:
            st.write("🔍 Records found in 'av':", result_av)
            st.write("🔍 Records found in 'archive':", result_archive)

            # ✅ Proceed with deletion
            delete_query_av = """
                DELETE FROM av WHERE date = %s AND shift = %s AND machine = %s
            """
            cur.execute(delete_query_av, (date, shift_type, selected_machine))

            delete_query_archive = """
                DELETE FROM archive WHERE "Date" = %s AND "Machine" = %s AND "Day/Night/plan" = %s
            """
            cur.execute(delete_query_archive, (date, selected_machine, shift_type))

            conn.commit()  # ✅ Commit changes

            st.success("✅ Existing records deleted. You can proceed with new data entry.")
            st.session_state.proceed_clicked = False  # Reset proceed state

    except Exception as e:
        conn.rollback()  # ✅ Rollback in case of error
        st.error(f"❌ Error deleting records: {e}")

if col2.button("🔄 Change Selection"):
    st.warning("🔄 Please modify the Date, Shift Type, or Machine to proceed.")
    st.session_state.proceed_clicked = False  # Reset proceed state
    st.stop()  # Prevents further execution

else:
    st.success("✅ No existing record found. You can proceed with the form.")

cur.close()
conn.close()  # ✅ Ensure connection is closed

    
shift_duration = st.selectbox("Shift Duration", [""] + shift_durations, index=0, key="shift_duration")
    
    # Downtime inputs with comments
st.subheader("Downtime (hours)")
downtime_data = {}
downtime_types = ["Maintenance DT", "Production DT", "Material DT", "Utility DT", "QC DT", "Cleaning DT", "QA DT", "Changeover DT"]
for dt_type in downtime_types:
        col1, col2 = st.columns(2)
        with col1:
            downtime_data[dt_type] = st.number_input(dt_type, min_value=0.0, step=0.1, format="%.1f")
        with col2:
            if downtime_data[dt_type] > 0:
                downtime_data[dt_type + "_comment"] = st.text_area(f"Comment for {dt_type}", placeholder="Enter comment here (required for downtime)")
            else:
                downtime_data[dt_type + "_comment"] = ""

if "product_batches" not in st.session_state:
    st.session_state.product_batches = {}

selected_product = st.selectbox("Select Product", [""] + product_list, index=0, key="selected_product")

# Allow adding batches for multiple products
if selected_product:
    if selected_product not in st.session_state.product_batches:
        st.session_state.product_batches[selected_product] = []
with st.form("batch_entry_form"):
    batch = st.text_input("Batch Number")
    quantity = st.number_input("Production Quantity", min_value=0.0, step=0.1, format="%.1f")
    time_consumed = st.number_input("Time Consumed (hours)", min_value=0.0, step=0.1, format="%.1f")
    add_batch = st.form_submit_button("Add Batch")

    if add_batch:
        if selected_product:
            if len(st.session_state.product_batches[selected_product]) < 5:
                st.session_state.product_batches[selected_product].append({
                    "batch": batch,
                    "quantity": quantity,
                    "time_consumed": time_consumed
                })
            else:
                st.error(f"You can add a maximum of 5 batches for {selected_product}.")
        else:
            st.error("Please select a product before adding a batch.")
    # Display added batches for the selected product with delete buttons
for product, batch_list in st.session_state.product_batches.items():
    if batch_list:  # Only show if there are batches
        st.subheader(f"Added Batches for {product}:")
        
             # Display table headers
        cols = st.columns(4)
        cols[0].write("Batch")
        cols[1].write("Quantity")
        cols[2].write("Time Consumed")
        cols[3].write("Delete")

        # Ensure batch_data exists
        batches_to_delete = []
        for i, batch in enumerate(batch_list):
            cols[0].write(batch["batch"])
            cols[1].write(batch["quantity"])
            cols[2].write(batch["time_consumed"])
            
            # Delete button
            if cols[3].button("Delete", key=f"delete_{product}_{i}"):
                batches_to_delete.append(i)

        # Remove selected batches
        for i in sorted(batches_to_delete, reverse=True):
            del st.session_state.product_batches[product][i]
            st.rerun()



from sqlalchemy.sql import text  # Import SQL text wrapper

# Ensure session state variables exist
if "show_confirmation" not in st.session_state:
    st.session_state.show_confirmation = False
if "replace_data" not in st.session_state:
    st.session_state.replace_data = False
if "restart_form" not in st.session_state:
    st.session_state.restart_form = False
if "submitted" not in st.session_state:
    st.session_state.submitted = False  # Tracks if report is submitted

# Function to update session state safely
def set_replace_data():
    st.session_state.replace_data = True

def set_restart_form():
    st.session_state.restart_form = True


# Validation: Check if comments are provided for downtime entries
missing_comments = [dt_type for dt_type in downtime_types if downtime_data[dt_type] > 0 and not downtime_data[dt_type + "_comment"]]
if missing_comments:
    st.error(f"Please provide comments for the following downtime types: {', '.join(missing_comments)}")
else:     
    st.write(f"Machine: {selected_machine}")
    st.write(f"Date: {date}")
    st.write(f"Shift Type: {shift_type}")
    st.write(f"Shift Duration: {shift_duration}")
          

 
   # Construct downtime records first
downtime_records = []
for dt_type in downtime_types:
    if downtime_data[dt_type] > 0:
        downtime_records.append({
            "Date": date,
            "Machine": selected_machine,
            "Day/Night/plan": shift_type,
            "Activity": dt_type,
            "time": downtime_data[dt_type],
            "Product": "",
            "batch number": "",
            "quantity": "",
            "comments": downtime_data[dt_type + "_comment"],
            "rate": "",
            "standard rate": "",
            "efficiency": "",
        })

# Compute efficiency for production records
efficiencies = []
production_records = []
missing_rates = False  # Track if any standard rate is missing

for product, batch_list in st.session_state.get("product_batches", {}).items():
    for batch in batch_list:
        rate = Decimal(batch["quantity"]) / Decimal(batch["time_consumed"]) if batch["time_consumed"] != 0 else Decimal("0")
        standard_rate = get_standard_rate(product, selected_machine)

        if standard_rate is None:
            missing_rates = True  # Mark that there's an issue
        else:
            efficiency = rate / standard_rate if standard_rate != 0 else 0
            efficiencies.append(efficiency)

            production_records.append({
                "Date": date,
                "Machine": selected_machine,
                "Day/Night/plan": shift_type,
                "Activity": "Production",
                "time": Decimal(batch["time_consumed"]),  # ✅ Convert to Decimal
                "Product": product,
                "batch number": batch["batch"],
                "quantity": Decimal(batch["quantity"]),  # ✅ Store as Decimal
                "comments": "",
                "rate": Decimal(rate),  # ✅ Convert rate to Decimal
                "standard rate": Decimal(standard_rate),  # ✅ Convert standard rate
                "efficiency": Decimal(efficiency),  # ✅ Convert efficiency
            })

# 🚨 Prevent Saving if Any Standard Rate is Missing
if missing_rates:
    st.error("❌ Cannot save data. Please update the correct standard rate in the database for all products before proceeding.")
    st.stop()  # Stop execution to prevent saving invalid data

# Calculate average efficiency once at the end
average_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 0

# Combine downtime and production records into one DataFrame
archive_df = pd.DataFrame(downtime_records + production_records)

            # Construct av_df
total_production_time = sum(
    batch["time_consumed"] for product, batch_list in st.session_state.product_batches.items() for batch in batch_list
)

filtered_shift = shifts_df.loc[shifts_df['code'] == shift_duration, 'working hours']

if not filtered_shift.empty:
    standard_shift_time = filtered_shift.iloc[0]
else:
    st.error(f"⚠️ Shift duration '{shift_duration}' not found in shifts.csv.")
    standard_shift_time = None  # Set default value or handle gracefully


if shift_duration == "partial":
    total_downtime = sum(downtime_data.values()) - sum(1 for key in downtime_data if "_comment" in key)
    availability = total_production_time / (total_production_time + total_downtime) if (total_production_time + total_downtime) != 0 else 0
else:
    # Ensure total_production_time and standard_shift_time have valid values
    if total_production_time is None or standard_shift_time is None:
        availability = 0  # Default value when form is empty
    else:
        availability = total_production_time / standard_shift_time if standard_shift_time != 0 else 0

OEE = Decimal("0.99") * Decimal(availability) * Decimal(average_efficiency)
av_row = {
                    "date": date,
                    "machine": selected_machine,
                    "shift type": shift_duration,
                    "hours": standard_shift_time,
                    "shift": shift_type,
                    "T.production time": total_production_time,
                    "Availability": availability,
                    "Av Efficiency": average_efficiency,
                    "OEE": OEE,
}
av_df = pd.DataFrame([av_row])

# Store submitted data in session state
st.session_state.submitted_archive_df = archive_df
st.session_state.submitted_av_df = av_df

# Display submitted data
for col in ["quantity", "rate", "standard rate", "efficiency"]:
    # ✅ Ensure column exists before converting
    if col in st.session_state.submitted_archive_df.columns:
        # ✅ Convert column to numeric safely, replacing errors with NaN
        st.session_state.submitted_archive_df[col] = pd.to_numeric(
            st.session_state.submitted_archive_df[col], errors="coerce"
        ).fillna(0.0)  # Replace NaN values with 0.0

    # ✅ Ensure column exists before converting in `submitted_av_df`
    if col in st.session_state.submitted_av_df.columns:
        st.session_state.submitted_av_df[col] = pd.to_numeric(
            st.session_state.submitted_av_df[col], errors="coerce"
        ).fillna(0.0)
st.subheader("Submitted Archive Data")
st.dataframe(st.session_state.submitted_archive_df)
  
st.subheader("Submitted AV Data")
st.dataframe(st.session_state.submitted_av_df)   
           # Compute total recorded time (downtime + production time)
total_production_time = sum(
    batch["time_consumed"] for product, batch_list in st.session_state.product_batches.items() for batch in batch_list
)
total_downtime = sum(downtime_data[dt] for dt in downtime_types)
total_recorded_time = total_production_time + total_downtime

# Fetch standard shift time
try:
    if shift_duration == "partial":
        standard_shift_time = None  # No standard time for partial shift
    else:
        standard_shift_time = shifts_df.loc[shifts_df['code'] == shift_duration, 'working hours'].iloc[0]
except IndexError:
    st.error("Shift duration not found in shifts.csv")
    standard_shift_time = 0  # Default to 0 to avoid None issues

# Compute total recorded time (downtime + production time)
# Ensure selected_product is valid before accessing product_batches
if selected_product and selected_product in st.session_state.product_batches:
    total_production_time = sum(batch["time_consumed"] for batch in st.session_state.product_batches[selected_product])
else:
    total_production_time = 0  # Default value when no product is selected

total_downtime = sum(downtime_data[dt] for dt in downtime_types)
total_recorded_time = total_production_time + total_downtime

# Special check for "partial" shift
if shift_duration == "partial":
    if total_recorded_time > 7:
        st.error("⚠️ Total recorded time cannot exceed 7 hours for a partial shift!")
    st.warning("⏳ Shift visualization is not available for 'partial' shifts.")
else:
    # Only show visualization if shift is NOT "partial"
    st.subheader("Shift Time Utilization")
    fig, ax = plt.subplots(figsize=(5, 2))

    # Bar Chart - Only add standard shift time if it's not None
    ax.barh(["Total Time"], [total_recorded_time], color="blue", label="Recorded Time")

    if standard_shift_time is not None:
        ax.barh(["Total Time"], [standard_shift_time], color="gray", alpha=0.5, label="Shift Standard Time")

    # Ensure limits are set correctly
    valid_times = [total_recorded_time]
    if standard_shift_time is not None:
        valid_times.append(standard_shift_time)

    # Set x-axis limits only if valid values exist
    if valid_times:
        ax.set_xlim(0, max(valid_times) * 1.2)

    ax.set_xlabel("Hours")
    ax.legend()

    # Display Chart
    st.pyplot(fig)

    # Display numeric comparison
    st.write(f"**Total Recorded Time:** {total_recorded_time:.2f} hrs")
    if standard_shift_time is not None:
        st.write(f"**Standard Shift Time:** {standard_shift_time:.2f} hrs")

    # Warnings
    if standard_shift_time is not None:
        if total_recorded_time > standard_shift_time:
            st.warning("⚠️ Total recorded time exceeds the standard shift time!")
        elif total_recorded_time < 0.75 * standard_shift_time:
            st.warning("⚠️ Recorded time is less than 75% of the standard shift time.")

         # xchecks & Approve and Save 
    
if st.button("Approve and Save"):
    # 🚨 Check if any standard rate is missing
    if missing_rates:
        st.error("❌ Cannot save data. Please update the correct standard rate in the database before proceeding.")
    else:
        conn = get_db_connection()  # ✅ Get the database connection
        if not conn:
            st.error("❌ Database connection failed. Please check credentials and try again.")
            st.stop()

        cur = conn.cursor()  # ✅ Use cursor for executing queries

        try:
            # 🚨 Check for duplicate entries in the database
            query = """
                SELECT COUNT(*) FROM av 
                WHERE date = %s AND "shift type" = %s AND machine = %s
            """

            cur.execute(query, (date, shift_type, selected_machine))
            result = cur.fetchone()

            if result and result[0] > 0:  # If a record already exists
                st.warning("⚠️ A report for this date, shift type, and machine already exists. Modify or confirm replacement.")
            else:
                st.success("✅ No existing record found. Proceeding with approval.")

                # Clean DataFrames before saving
                archive_df = clean_dataframe(st.session_state.submitted_archive_df.copy())
                av_df = clean_dataframe(st.session_state.submitted_av_df.copy())

                # Get shift standard time
                standard_shift_time = shifts_df.loc[shifts_df['code'] == shift_duration, 'working hours'].iloc[0]

                # Validation checks
                total_recorded_time = archive_df["time"].sum()
                efficiency_invalid = (archive_df["efficiency"] > 1).any()
                time_exceeds_shift = total_recorded_time > standard_shift_time
                time_below_75 = total_recorded_time < (0.75 * standard_shift_time)

                # 🚨 Validation Errors
                if efficiency_invalid:
                    st.error("❌ Efficiency must not exceed 1. Please review and modify the data.")
                elif time_exceeds_shift:
                    st.error(f"❌ Total recorded time ({total_recorded_time} hrs) exceeds shift standard time ({standard_shift_time} hrs). Modify the data.")
                elif time_below_75:
                    st.error(f"❌ Total recorded time ({total_recorded_time} hrs) is less than 75% of shift standard time ({0.75 * standard_shift_time} hrs). Modify the data.")
                else:
                    try:
                        # ✅ Save to database using SQL INSERT
                        for _, row in archive_df.iterrows():
                            row["time"] = float(row["time"]) if row["time"] else None
                            row["efficiency"] = float(row["efficiency"]) if row["efficiency"] else None
                            row["quantity"] = float(row["quantity"]) if row["quantity"] else None
                            row["rate"] = float(row["rate"]) if row["rate"] else None
                            row["standard rate"] = float(row["standard rate"]) if row["standard rate"] else None

                        cur.execute("""
                            INSERT INTO archive ("Date", "Machine", "Day/Night/plan", "time", "efficiency", "quantity", "rate", "standard rate")
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            row["Date"], 
                            row["Machine"], 
                            row["Day/Night/plan"], 
                            row["time"],  
                            row["efficiency"],
                            row["quantity"],  
                            row["rate"],  
                            row["standard rate"]
                        ))

                        for _, row in av_df.iterrows():
                            row["hours"] = float(row["hours"]) if row["hours"] else None
                            row["T.production time"] = float(row["T.production time"]) if row["T.production time"] else None
                            row["Availability"] = float(row["Availability"]) if row["Availability"] else None
                            row["Av Efficiency"] = float(row["Av Efficiency"]) if row["Av Efficiency"] else None
                            row["OEE"] = float(row["OEE"]) if row["OEE"] else None

                            cur.execute("""
                                INSERT INTO av (date, shift, machine, "shift type", hours, "T.production time", Availability, "Av Efficiency", OEE)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    row["date"],
                                    row["shift"],
                                    row["machine"],
                                    row["shift type"],  
                                    row["hours"],
                                    row["T.production time"],  
                                    row["Availability"],
                                    row["Av Efficiency"],  
                                    row["OEE"]
                                ))

                    conn.commit()  # ✅ Commit the changes
                    st.success("✅ Data saved to database successfully!")

                except Exception as e:  # ✅ Fixed indentation
                    conn.rollback()  # ✅ Rollback changes in case of an error
                    st.error(f"❌ Error saving data: {e}")
