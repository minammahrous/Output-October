import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Database connection URL
DB_URL = "postgresql://neondb_owner:npg_QyWNO1qFf4do@ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech/neondb?sslmode=require"
engine = create_engine(DB_URL)

# Function to fetch products list
def fetch_products():
    """Fetch product names and IDs from the database."""
    query = "SELECT id, name FROM products ORDER BY name"
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        return df
    except Exception as e:
        st.error(f"Error fetching products: {e}")
        return pd.DataFrame()

# Function to fetch product details by ID
def fetch_product_details(product_id):
    """Fetch details of a selected product."""
    query = "SELECT name, batch_size, units_per_box, primary_units_per_box, oracle_code FROM products WHERE id = :id"
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn, params={"id": product_id})
        return df.iloc[0] if not df.empty else None
    except Exception as e:
        st.error(f"Error fetching product details: {e}")
        return None

# Function to insert or update product
def save_product(product_id, name, batch_size, units_per_box, primary_units_per_box, oracle_code):
    """Insert a new product or update an existing one."""
    try:
        with engine.connect() as conn:
            if product_id:
                # Update existing product
                query = """
                    UPDATE products 
                    SET name = :name, batch_size = :batch_size, units_per_box = :units_per_box, 
                        primary_units_per_box = :primary_units_per_box, oracle_code = :oracle_code 
                    WHERE id = :id
                """
                conn.execute(text(query), {
                    "id": product_id, "name": name, "batch_size": batch_size,
                    "units_per_box": units_per_box, "primary_units_per_box": primary_units_per_box,
                    "oracle_code": oracle_code
                })
            else:
                # Insert new product
                query = """
                    INSERT INTO products (name, batch_size, units_per_box, primary_units_per_box, oracle_code) 
                    VALUES (:name, :batch_size, :units_per_box, :primary_units_per_box, :oracle_code)
                """
                conn.execute(text(query), {
                    "name": name, "batch_size": batch_size, 
                    "units_per_box": units_per_box, "primary_units_per_box": primary_units_per_box, 
                    "oracle_code": oracle_code
                })
            conn.commit()
        st.success("Product saved successfully!")
        st.rerun()  # Refresh the page after saving
    except Exception as e:
        st.error(f"Error saving product: {e}")

# Streamlit UI
st.title("Manage Products")

# Button to open the form
if st.button("Edit Product Definition"):
    st.session_state["show_form"] = True  # Store state to show form

# Show form only if button is clicked
if st.session_state.get("show_form", False):
    st.markdown("### Add/Edit Product Details")
    st.write("Modify product name, batch size, units per box, and Oracle code below.")

    # Fetch products and show dropdown
    products = fetch_products()
    product_options = {row["name"]: row["id"] for _, row in products.iterrows()}
    selected_product = st.selectbox("Select a product to edit (or leave blank to add a new one)", ["New Product"] + list(product_options.keys()))

    # Load existing product data if selected
    if selected_product != "New Product":
        product_id = product_options[selected_product]
        product_data = fetch_product_details(product_id)
    else:
        product_id = None
        product_data = None

    # Product input form
    name = st.text_input("Product Name", value=product_data["name"] if product_data is not None else "")
    batch_size = st.number_input("Batch Size", min_value=1.0, value=float(product_data["batch_size"]) if product_data is not None and not product_data.empty else 1.0)
    units_per_box = st.number_input("Units per Box", min_value=1.0, value=float(product_data["units_per_box"]) if product_data is not None and not product_data.empty else 1.0)
    primary_units_per_box = st.number_input("Primary Units per Box", min_value=1.0, value=float(product_data["primary_units_per_box"]) if product_data is not None and not product_data.empty else 1.0)

    oracle_code = st.text_input("Oracle Code (Optional)", value=product_data["oracle_code"] if product_data is not None else "")

    # Save button
    if st.button("Save Product"):
        if name and batch_size and units_per_box and primary_units_per_box:
            save_product(product_id, name, batch_size, units_per_box, primary_units_per_box, oracle_code)
        else:
            st.error("Please fill in all mandatory fields.")
