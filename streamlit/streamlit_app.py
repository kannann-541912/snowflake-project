import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Data Platform", layout="wide")
st.title("Data Platform Dashboard")

session = get_active_session()

# Customer order summary
st.header("Customer Order Summary")

df = session.sql("""
    SELECT
        CUSTOMER_ID,
        NAME,
        TOTAL_ORDERS,
        LIFETIME_VALUE,
        LAST_ORDER_DATE
    FROM SANDBOX.TPCH.CUSTOMER_ORDER_SUMMARY
    ORDER BY LIFETIME_VALUE DESC
    LIMIT 50
""").to_pandas()

col1, col2, col3 = st.columns(3)
col1.metric("Total Customers", len(df))
col2.metric("Total Orders", int(df["TOTAL_ORDERS"].sum()))
col3.metric("Total Revenue", f"${df['LIFETIME_VALUE'].sum():,.2f}")

st.dataframe(df, use_container_width=True)
