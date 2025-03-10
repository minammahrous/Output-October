import streamlit as st
import psycopg2
import pandas as pd

# Database connection
DB_PARAMS = {
    "dbname": "neondb",
    "user": "your_username",
    "password": "your_password",
    "host": "ep-quiet-wave-a8pgbkwd-pooler.eastus2.azure.neon.tech",
    "port": "5432"
}

def get_connection():
    return psycopg2.connect(**DB_PARAMS)

# Fetch existing products
def fetch_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM products ORDER BY name")
    products = cur.fetchall()
    conn.close()
    return products

# Fetch product details
def fetch_product_details(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, batch_size, units_per_box, primary_units_per_box, oracle_code FROM products WHERE id = %s", (product_id,))
    product = cur.fetchone()
    conn.close()
    return product

# Add or update product
def save_product(product_id, name, batch_size, units_per_box, primary_units_per_box, oracle_code):
    conn = get_connection()
    cur = conn.cursor()
    
    if product_id:
        # Update existing product
        cur.execute("""
            UPDATE products 
            SET name=%s, batch_size=%s, units_per_box=%s, primary_units_per_box=%s, oracle_code=%s
            WHERE id=%s
        """, (name, batch_size, units_per_box, primary_units_per_box, oracle_code, product_id))
    else:
        # Insert new product
        cur.execute("""
            INSERT INTO products (name, batch_size, units_per_box, primary_units_per_box, oracle_code) 
            VALUES (%s, %s, %s, %s, %s)
        """, (name, batch_size, units_per_box, primary_units_per_box, oracle_code))
    
    conn.commit()
    conn.close()

# Streamlit UI
st.title("Manage Products")

# Select existing product or add new
products = fetch_products()
product_options = {name: id for id, name in products}
selected_product = st.selectbox("Select a product to edit (or leave blank to add a new one)", ["New Product"] + list(product_options.keys()))

# Load existing product data if selected
if selected_product != "New Product":
    product_id = product_options[selected_product]
    product_data = fetch_product_details(product_id)
else:
    product_id = None
    product_data = ("", "", "", "", "")

# Product input form
name = st.text_input("Product Name", value=product_data[0])
batch_size = st.number_input("Batch Size", min_value=1, value=product_data[1] if product_data[1] else 1)
units_per_box = st.number_input("Units per Box", min_value=1, value=product_data[2] if product_data[2] else 1)
primary_units_per_box = st.number_input("Primary Units per Box", min_value=1, value=product_data[3] if product_data[3] else 1)
oracle_code = st.text_input("Oracle Code (Optional)", value=product_data[4])

if st.button("Save Product"):
    if name and batch_size and units_per_box and primary_units_per_box:
        save_product(product_id, name, batch_size, units_per_box, primary_units_per_box, oracle_code)
        st.success("Product saved successfully!")
        st.experimental_rerun()
    else:
        st.error("Please fill in all mandatory fields.")

