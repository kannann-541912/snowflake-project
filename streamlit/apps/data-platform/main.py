import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parents[2]))

import streamlit as st
from shared.utils import get_session, fmt_currency, fmt_number

st.set_page_config(page_title="Data Platform", layout="wide")
st.title("Data Platform Dashboard")

session = get_session()

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
col1.metric("Total Customers", fmt_number(len(df)))
col2.metric("Total Orders",    fmt_number(df["TOTAL_ORDERS"].sum()))
col3.metric("Total Revenue",   fmt_currency(df["LIFETIME_VALUE"].sum()))

st.dataframe(df, use_container_width=True)
