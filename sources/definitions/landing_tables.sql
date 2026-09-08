-- ============================================================
-- Landing tables — raw data loaded by COPY INTO from stages
-- Managed by DCM. All names use {{env_suffix}} templating.
-- ============================================================

-- Raw customers landing table
DEFINE TABLE SANDBOX{{env_suffix}}.TPCH_LANDING.CUSTOMERS_RAW (
    CUSTOMER_ID     NUMBER,
    NAME            VARCHAR(100),
    EMAIL           VARCHAR(255),
    CREATED_AT      VARCHAR(30),
    _LOADED_AT      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _SOURCE_FILE    VARCHAR(500)
)
    COMMENT = 'Raw customer data loaded from external stage'
    CHANGE_TRACKING = TRUE;

-- Raw orders landing table
DEFINE TABLE SANDBOX{{env_suffix}}.TPCH_LANDING.ORDERS_RAW (
    ORDER_ID        NUMBER,
    CUSTOMER_ID     NUMBER,
    ORDER_DATE      VARCHAR(20),
    TOTAL_AMOUNT    VARCHAR(20),
    STATUS          VARCHAR(20),
    _LOADED_AT      TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    _SOURCE_FILE    VARCHAR(500)
)
    COMMENT = 'Raw order data loaded from external stage'
    CHANGE_TRACKING = TRUE;
