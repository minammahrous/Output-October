import streamlit as st
import datetime
import pandas as pd
import csv
import os
from sqlalchemy import create_engine
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# Database connection
DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
engine = create_engine(DB_URL)
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
# Read machine list from CSV
machine_list = []
try:
    with open("machines.csv", "r") as file:
        reader = csv.reader(file)
        for row in reader:
            machine_list.append(row[0])
except FileNotFoundError:
    st.error("machines.csv file not found. Please create the file.")
except Exception as e:
    st.error(f"An error occurred reading machines.csv: {e}")

# Read product list from CSV
product_list = []
try:
    with open("products.csv", "r") as file:
        reader = csv.reader(file)
        for row in reader:
            product_list.append(row[0])
except FileNotFoundError:
    st.error("products.csv file not found. Please create the file.")
except Exception as e:
    st.error(f"An error occurred reading products.csv: {e}")

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
# Ensure downtime_data is initialized in session state early
if "downtime_data" not in st.session_state:
    st.session_state.downtime_data = {}

# Assign session state data to a variable
downtime_data = st.session_state.downtime_data
shift_types = ["Day", "Night", "Plan"]
date = st.date_input("Date", None, key="date")  
selected_machine = st.selectbox("Select Machine", [""] + machine_list, index=0, key="machine")
shift_type = st.selectbox("Shift Type", [""] + shift_types, index=0, key="shift_type")
    # Ensure selections are made before querying the database
if date and shift_type and selected_machine:
    # Check if a record exists for the selected combination in the 'av' table
    query = text("""
        SELECT COUNT(*) FROM av 
        WHERE date = :date AND "shift type" = :shift_type AND machine = :machine
    """)

    with engine.connect() as conn:
        result = conn.execute(query, {"date": date, "shift_type": shift_type, "machine": selected_machine}).fetchone()

    if result and result[0] > 0:  # If a record already exists
        st.warning("⚠️ A report for this Date, Shift Type, and Machine already exists. Please choose an action.")

        col1, col2 = st.columns(2)
        if col1.button("🗑️ Delete Existing Data and Continue"):
            # Delete from both tables
            delete_query_av = text("""
                DELETE FROM av WHERE date = :date AND "shift type" = :shift_type AND machine = :machine
            """)
            delete_query_archive = text("""
                DELETE FROM archive WHERE date = :date AND machine = :machine AND "Day/Night/plan" = :shift_type
            """)

            with engine.connect() as conn:
                conn.execute(delete_query_av, {"date": date, "shift_type": shift_type, "machine": selected_machine})
                conn.execute(delete_query_archive, {"date": date, "shift_type": shift_type, "machine": selected_machine})
                conn.commit()

            st.success("✅ Existing records deleted. You can proceed with new data entry.")

        if col2.button("🔄 Change Selection"):
            st.warning("Please modify the Date, Shift Type, or Machine to proceed.")
            st.stop()  # Prevents further execution

        st.stop()  # Prevents user from entering more data until they take action

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

    # Initialize session state for product-specific batch data
    if "product_batches" not in st.session_state:
        st.session_state.product_batches = {}

    # Ensure selected_product is initialized
selected_product = st.selectbox("Select Product", [""] + product_list, index=0, key="product")

# Initialize session state for product-specific batch data
if "product_batches" not in st.session_state:
    st.session_state.product_batches = {}

# Safely check if selected_product has been chosen
if selected_product and selected_product in st.session_state.product_batches:
    batch_data = st.session_state.product_batches[selected_product]

    if batch_data:  # check if batch_data is not empty
        st.subheader(f"Added Batches for {selected_product}:")
        cols = st.columns(4)  # Fixed number of columns

        # Header row
        cols[0].write("Batch")
        cols[1].write("Quantity")
        cols[2].write("Time Consumed")
        cols[3].write("Delete")

        # Data rows and delete buttons
        batches_to_delete = []  # create a list to store indexes to delete
        for i, batch in enumerate(batch_data):
            cols[0].write(batch["batch"])
            cols[1].write(batch["quantity"])
            cols[2].write(batch["time_consumed"])
            if cols[3].button("Delete", key=f"delete_{selected_product}_{i}"):
                batches_to_delete.append(i)  # add index to delete list

        # Delete the batches after the loop, in reverse order to avoid index issues.
        for i in sorted(batches_to_delete, reverse=True):
            del st.session_state.product_batches[selected_product][i]
            st.rerun()  # refresh after any deletion.

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
          

 
    # Construct archive_df (Downtime records)
    archive_data = []
    for dt_type in downtime_types:
        if downtime_data[dt_type] > 0:
            archive_row = {
            "Date": date,
            "Machine": selected_machine,
            "Day/Night/plan": shift_type,
            "Activity": dt_type,
            "time": downtime_data[dt_type],
            "Product": "",
            "batch number": "",
            "quantity": "",
            "commnets": downtime_data[dt_type + "_comment"],
            "rate": "",
            "standard rate": "",
            "efficiency": "",
             }
            archive_data.append(archive_row)
            archive_df = pd.DataFrame(archive_data)

            # Construct archive_df (Production batch records)
            try:
                rates_df = pd.read_csv("rates.csv")
                for batch_data in st.session_state.product_batches[selected_product]:
                    rate = batch_data["quantity"] / batch_data["time_consumed"]
                    try:
                        standard_rate = rates_df.loc[(rates_df['Product'] == selected_product) & (rates_df['Machine'] == selected_machine), 'Rate'].iloc[0]
                    except IndexError:
                        st.error(f"No rate found for Product: {selected_product}, Machine: {selected_machine}")
                        standard_rate = 0  # or some default value
                    except KeyError:
                        st.error("The column 'Rate' does not exist in rates.csv")
                        standard_rate = 0  # or some default value
                    efficiency = rate / standard_rate if standard_rate != 0 else 0
                    archive_row = {
                        "Date": date,
                        "Machine": selected_machine,
                        "Day/Night/plan": shift_type,
                        "Activity": "Production",
                        "time": batch_data["time_consumed"],
                        "Product": selected_product,
                        "batch number": batch_data["batch"],
                        "quantity": batch_data["quantity"],
                        "commnets": "",
                        "rate": rate,
                        "standard rate": standard_rate,
                        "efficiency": efficiency,
                    }
                    archive_df = pd.concat([archive_df, pd.DataFrame([archive_row])], ignore_index=True)
            except FileNotFoundError:
                st.error("rates.csv was not found")

            # Construct av_df
            try:
                total_production_time = sum([batch["time_consumed"] for batch in st.session_state.product_batches[selected_product]])
                standard_shift_time = shifts_df.loc[shifts_df['code'] == shift_duration, 'working hours'].iloc[0]

                if shift_duration == "partial":
                    total_downtime = sum(downtime_data.values()) - sum(1 for key in downtime_data if "_comment" in key)
                    availability = total_production_time / (total_production_time + total_downtime) if (total_production_time + total_downtime) != 0 else 0
                else:
                    availability = total_production_time / standard_shift_time if standard_shift_time != 0 else 0

                efficiencies = [batch["quantity"] / (batch["time_consumed"] * rates_df.loc[(rates_df['Product'] == selected_product) & (rates_df['Machine'] == selected_machine), 'Rate'].iloc[0]) if (rates_df.loc[(rates_df['Product'] == selected_product) & (rates_df['Machine'] == selected_machine), 'Rate'].iloc[0] != 0 and batch["time_consumed"] != 0) else 0 for batch in st.session_state.product_batches[selected_product]]
                average_efficiency = sum(efficiencies) / len(efficiencies) if efficiencies else 0
                OEE = 0.99 * availability * average_efficiency
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
            except FileNotFoundError:
                st.error("shifts.csv or rates.csv was not found")

            # Store submitted data in session state
            st.session_state.submitted_archive_df = archive_df
            st.session_state.submitted_av_df = av_df

            # Display submitted data
            st.subheader("Submitted Archive Data")
            st.dataframe(st.session_state.submitted_archive_df)
            st.subheader("Submitted AV Data")
            st.dataframe(st.session_state.submitted_av_df)
           # Compute total recorded time (downtime + production time)
total_production_time = sum(batch["time_consumed"] for batch in st.session_state.product_batches[selected_product])
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
total_production_time = sum(batch["time_consumed"] for batch in st.session_state.product_batches[selected_product])
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
    try:
        # Check for duplicate entries in the database
        query = text("""
        SELECT COUNT(*) FROM av 
        WHERE date = :date AND "shift type" = :shift_type AND machine = :machine
        """)

        with engine.connect() as conn:
            result = conn.execute(query, {"date": date, "shift_type": shift_type, "machine": selected_machine}).fetchone()

        if result and result[0] > 0:  # If a record already exists
            st.warning("A report for this date, shift type, and machine already exists. Modify or confirm replacement.")
        else:
            st.success("No existing record found. Proceeding with approval.")

            # Clean DataFrames before using them
            archive_df = clean_dataframe(st.session_state.submitted_archive_df.copy())
            av_df = clean_dataframe(st.session_state.submitted_av_df.copy())

            # Get shift standard time
            standard_shift_time = shifts_df.loc[shifts_df['code'] == shift_duration, 'working hours'].iloc[0]

            # Validation checks
            total_recorded_time = archive_df["time"].sum()
            efficiency_invalid = (archive_df["efficiency"] > 1).any()
            time_exceeds_shift = total_recorded_time > standard_shift_time
            time_below_75 = total_recorded_time < (0.75 * standard_shift_time)

            if efficiency_invalid:
                st.error("Efficiency must not exceed 1. Please review and modify the data.")
            elif time_exceeds_shift:
                st.error(f"Total recorded time ({total_recorded_time} hrs) exceeds shift standard time ({standard_shift_time} hrs). Modify the data.")
            elif time_below_75:
                st.error(f"Total recorded time ({total_recorded_time} hrs) is less than 75% of shift standard time ({0.75 * standard_shift_time} hrs). Modify the data.")
            else:
                # Save cleaned data to PostgreSQL
                archive_df.to_sql("archive", engine, if_exists="append", index=False)
                av_df.to_sql("av", engine, if_exists="append", index=False)
                st.success("Data saved to database successfully!")

    except Exception as e:
        st.error(f"Error saving data: {e}")

