-- View definitions
-- All object names use {{env_suffix}} for environment-aware naming.

DEFINE VIEW SANDBOX{{env_suffix}}.TPCH.CUSTOMER_ORDER_SUMMARY AS
    SELECT
        c.CUSTOMER_ID,
        c.NAME,
        COUNT(o.ORDER_ID) AS TOTAL_ORDERS,
        SUM(o.TOTAL_AMOUNT) AS LIFETIME_VALUE,
        MAX(o.ORDER_DATE) AS LAST_ORDER_DATE
    FROM SANDBOX{{env_suffix}}.TPCH.CUSTOMERS c
    LEFT JOIN SANDBOX{{env_suffix}}.TPCH.ORDERS o
        ON c.CUSTOMER_ID = o.CUSTOMER_ID
    GROUP BY c.CUSTOMER_ID, c.NAME;
