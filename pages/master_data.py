import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Database connection URL
DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
engine = create_engine(DB_URL, pool_pre_ping=True)
st.title("Edit Product Standard Rate")

if st.button("Edit Product Standard Rate"):
    st.session_state["show_rates_form"] = True
if "show_rates_form" not in st.session_state:
    st.session_state["show_rates_form"] = False

# Fetch products list from the products table
def fetch_products():
    """Fetch product names from the products table."""
    query = "SELECT name FROM products ORDER BY name"
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        return df
    except Exception as e:
        st.error(f"Error fetching products: {e}")
        return pd.DataFrame()

# Fetch rates for a product, ensuring machines are always shown
def fetch_rates(product):
    """Fetch existing rates for a product, including machines that may not have rates yet."""
    query = """
    SELECT m.name AS machine, COALESCE(r.standard_rate, 0) AS standard_rate, m.qty_uom
    FROM machines m
    LEFT JOIN rates r ON m.name = r.machine AND r.product = :product
    ORDER BY m.name
    """
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params={"product": product})
        return df
    except Exception as e:
        st.error(f"Error fetching rates: {e}")
        return pd.DataFrame()

# Save updated rates
def save_rates(product, updated_rates):
    try:
        with engine.connect() as conn:
            with conn.begin():
                for machine, rate in updated_rates.items():
                    query = """
                    INSERT INTO rates (product, machine, standard_rate) 
                    VALUES (:product, :machine, :rate) 
                    ON CONFLICT (product, machine) 
                    DO UPDATE SET standard_rate = EXCLUDED.standard_rate
                    """
                    conn.execute(text(query), {"product": product, "machine": machine, "rate": rate})
        st.success("Rates updated successfully!")
        st.rerun()
    except Exception as e:
        st.error(f"Error saving rates: {e}")

# Streamlit UI
st.title("Edit Product Standard Rate")

if st.button("Edit Product Standard Rate"):
    st.session_state["show_rates_form"] = True

if st.session_state.get("show_rates_form", False):
    products = fetch_products()
    product_list = products["name"].tolist()
    selected_product = st.selectbox("Select a product", ["Select"] + product_list)
    
    if selected_product != "Select":
        rates_df = fetch_rates(selected_product)
        
        # Convert existing rates to dictionary for easy updates
        existing_rates = {row["machine"]: row["standard_rate"] for _, row in rates_df.iterrows()}
        
        st.markdown("### Update Rates")
        updated_rates = {}
        
        for _, row in rates_df.iterrows():
            machine = row["machine"]
            qty_uom = row["qty_uom"]
            rate_value = existing_rates.get(machine, 0)
            updated_rate = st.number_input(f"{machine} (Rate in {qty_uom})", min_value=0.0, value=rate_value)
            if updated_rate != rate_value:
                updated_rates[machine] = updated_rate
        
        if updated_rates:
            st.markdown("### Summary of Changes")
            for machine, rate in updated_rates.items():
                st.write(f"{machine}: {rate}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Changes"):
                    save_rates(selected_product, updated_rates)
            with col2:
                if st.button("Cancel"):
                    st.session_state["show_rates_form"] = False
                    st.rerun()
