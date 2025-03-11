import streamlit as st
import pandas as pd
from db import get_db_connection

st.title("Manage Products & Standard Rates")

# Expander for Product Definition
with st.expander("Edit Product Definition", expanded=False):
    st.markdown("### Add/Edit Product Details")

    # Fetch products
    def fetch_products():
        """Fetch product names and IDs from the database."""
        query = "SELECT id, name FROM products ORDER BY name"
        conn = get_db_connection()
        if not conn:
            st.error("❌ Database connection failed.")
            return pd.DataFrame()
        
        try:
            df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Error fetching products: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    products = fetch_products()
    product_options = {row["name"]: row["id"] for _, row in products.iterrows()}
    selected_product = st.selectbox("Select a product", ["New Product"] + list(product_options.keys()))

    # Fetch product details
    def fetch_product_details(product_id):
        """Fetch details of a selected product."""
        query = "SELECT name, batch_size, units_per_box, primary_units_per_box, oracle_code FROM products WHERE id = %s"
        conn = get_db_connection()
        if not conn:
            return None
        
        try:
            df = pd.read_sql(query, conn, params=(product_id,))
            return df.iloc[0] if not df.empty else None
        except Exception as e:
            st.error(f"Error fetching product details: {e}")
            return None
        finally:
            conn.close()

    if selected_product != "New Product":
        product_id = product_options[selected_product]
        product_data = fetch_product_details(product_id)
    else:
        product_id = None
        product_data = None

    name = st.text_input("Product Name", value=product_data["name"] if product_data is not None else "")

    batch_size = st.number_input(
        "Batch Size",
        min_value=1.0,
        value=float(product_data["batch_size"]) if product_data is not None and pd.notna(product_data["batch_size"]) else 1.0
    )

    units_per_box = st.number_input(
        "Units per Box",
        min_value=1.0,
        value=float(product_data["units_per_box"]) if product_data is not None and pd.notna(product_data["units_per_box"]) else 1.0
    )

    primary_units_per_box = st.number_input(
        "Primary Units per Box",
        min_value=1.0,
        value=float(product_data["primary_units_per_box"]) if product_data is not None and pd.notna(product_data["primary_units_per_box"]) else 1.0
    )

    oracle_code = st.text_input("Oracle Code (Optional)", value=product_data["oracle_code"] if product_data is not None else "")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Product"):
            def save_product():
                """Save or update product details."""
                query = """
                    INSERT INTO products (name, batch_size, units_per_box, primary_units_per_box, oracle_code)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE 
                    SET batch_size = EXCLUDED.batch_size, units_per_box = EXCLUDED.units_per_box,
                        primary_units_per_box = EXCLUDED.primary_units_per_box, oracle_code = EXCLUDED.oracle_code
                """
                conn = get_db_connection()
                if not conn:
                    st.error("❌ Database connection failed.")
                    return
                
                try:
                    cur = conn.cursor()
                    cur.execute(query, (name, batch_size, units_per_box, primary_units_per_box, oracle_code))
                    conn.commit()
                    st.success("✅ Product saved successfully!")
                except Exception as e:
                    st.error(f"Error saving product: {e}")
                finally:
                    cur.close()
                    conn.close()

            save_product()
            st.rerun()

    with col2:
        if st.button("cancel"):
            st.rerun()

# Expander for Standard Rates
with st.expander("Edit Product Standard Rate", expanded=False):
    st.markdown("### Update Product Standard Rates")

    products = fetch_products()
    product_list = products["name"].tolist()
    selected_product = st.selectbox("Select a product", ["Select"] + product_list)

    def fetch_rates(product):
        """Fetch existing rates for a product."""
        query = """
        SELECT m.name AS machine, COALESCE(r.standard_rate, 0) AS standard_rate, m.qty_uom
        FROM machines m
        LEFT JOIN rates r ON m.name = r.machine AND r.product = %s
        ORDER BY m.name
        """
        conn = get_db_connection()
        if not conn:
            return pd.DataFrame()
        
        try:
            df = pd.read_sql(query, conn, params=(product,))
            return df
        except Exception as e:
            st.error(f"Error fetching rates: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    if selected_product != "Select":
        rates_df = fetch_rates(selected_product)

        updated_rates = {}
        for _, row in rates_df.iterrows():
            machine = row["machine"]
            qty_uom = row["qty_uom"]
            rate_value = row["standard_rate"]
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
                    def save_rates():
                        """Save updated rates."""
                        query = """
                        INSERT INTO rates (product, machine, standard_rate)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (product, machine) 
                        DO UPDATE SET standard_rate = EXCLUDED.standard_rate
                        """
                        conn = get_db_connection()
                        if not conn:
                            st.error("❌ Database connection failed.")
                            return
                        
                        try:
                            cur = conn.cursor()
                            for machine, rate in updated_rates.items():
                                cur.execute(query, (selected_product, machine, rate))
                            conn.commit()
                            st.success("✅ Rates updated successfully!")
                        except Exception as e:
                            st.error(f"Error saving rates: {e}")
                        finally:
                            cur.close()
                            conn.close()

                    save_rates()
                    st.rerun()

            with col2:
                if st.button("Cancel"):
                    st.rerun()
