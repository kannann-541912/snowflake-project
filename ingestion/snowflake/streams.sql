-- ============================================================
-- Snowflake Streams — Change Data Capture
-- Streams capture DML changes on source tables for downstream
-- processing by Snowflake Tasks or dbt incremental models.
-- Deployed via snow sql (not DCM — streams are not DCM-managed).
-- ============================================================

-- Stream on CUSTOMERS table: captures INSERT / UPDATE / DELETE
-- SHOW_INITIAL_ROWS = TRUE so first run processes all existing rows.
CREATE OR REPLACE STREAM SANDBOX.TPCH.CUSTOMERS_STREAM
    ON TABLE SANDBOX.TPCH.CUSTOMERS
    SHOW_INITIAL_ROWS = TRUE
    COMMENT = 'CDC stream on CUSTOMERS — feeds downstream transforms';

-- Stream on ORDERS table: append-only (orders are never updated)
CREATE OR REPLACE STREAM SANDBOX.TPCH.ORDERS_STREAM
    ON TABLE SANDBOX.TPCH.ORDERS
    APPEND_ONLY = TRUE
    COMMENT = 'Append-only CDC stream on ORDERS';

-- Streams on landing tables (feed into Snowflake Task DAG)
CREATE OR REPLACE STREAM SANDBOX.TPCH_LANDING.CUSTOMERS_RAW_STREAM
    ON TABLE SANDBOX.TPCH_LANDING.CUSTOMERS_RAW
    SHOW_INITIAL_ROWS = TRUE
    COMMENT = 'Stream on raw customers landing table';

CREATE OR REPLACE STREAM SANDBOX.TPCH_LANDING.ORDERS_RAW_STREAM
    ON TABLE SANDBOX.TPCH_LANDING.ORDERS_RAW
    APPEND_ONLY = TRUE
    COMMENT = 'Append-only stream on raw orders landing table';
