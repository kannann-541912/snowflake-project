-- Access control: Roles and Grants
-- All names use {{env_suffix}} for environment-aware naming.

DEFINE ROLE DATA_READER{{env_suffix}};

GRANT USAGE ON WAREHOUSE ANALYTICS_WH{{env_suffix}}
    TO ROLE DATA_READER{{env_suffix}};

GRANT SELECT ON TABLE SANDBOX{{env_suffix}}.TPCH.CUSTOMERS
    TO ROLE DATA_READER{{env_suffix}};

GRANT SELECT ON TABLE SANDBOX{{env_suffix}}.TPCH.ORDERS
    TO ROLE DATA_READER{{env_suffix}};

GRANT SELECT ON VIEW SANDBOX{{env_suffix}}.TPCH.CUSTOMER_ORDER_SUMMARY
    TO ROLE DATA_READER{{env_suffix}};
