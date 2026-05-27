-- ============================================================
-- Snowflake Streams — Change Data Capture
-- Streams capture DML changes on source tables for downstream
-- processing by Snowflake Tasks or dbt incremental models.
-- ============================================================

-- Stream on CUSTOMERS table: captures INSERT / UPDATE / DELETE
-- SHOW_INITIAL_ROWS = TRUE so first run processes all existing rows.
DEFINE STREAM SANDBOX.TPCH.CUSTOMERS_STREAM
    ON TABLE SANDBOX.TPCH.CUSTOMERS
    SHOW_INITIAL_ROWS = TRUE
    COMMENT = 'CDC stream on CUSTOMERS — feeds downstream transforms';

-- Stream on ORDERS table: append-only (orders are never updated)
DEFINE STREAM SANDBOX.TPCH.ORDERS_STREAM
    ON TABLE SANDBOX.TPCH.ORDERS
    APPEND_ONLY = TRUE
    COMMENT = 'Append-only CDC stream on ORDERS';

-- ============================================================
-- Landing tables — raw data loaded by COPY INTO from stages
-- ============================================================

-- Raw customers landing table
DEFINE TABLE SANDBOX.TPCH_LANDING.CUSTOMERS_RAW (
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
DEFINE TABLE SANDBOX.TPCH_LANDING.ORDERS_RAW (
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

-- ============================================================
-- Landing table streams — feed into Snowflake Task DAG
-- ============================================================

DEFINE STREAM SANDBOX.TPCH_LANDING.CUSTOMERS_RAW_STREAM
    ON TABLE SANDBOX.TPCH_LANDING.CUSTOMERS_RAW
    SHOW_INITIAL_ROWS = TRUE
    COMMENT = 'Stream on raw customers landing table';

DEFINE STREAM SANDBOX.TPCH_LANDING.ORDERS_RAW_STREAM
    ON TABLE SANDBOX.TPCH_LANDING.ORDERS_RAW
    APPEND_ONLY = TRUE
    COMMENT = 'Append-only stream on raw orders landing table';
