-- ============================================================
-- Snowflake Task DAG — Native Orchestration
-- This DAG runs AFTER Airflow loads raw files into landing tables.
-- Uses SYSTEM$STREAM_HAS_DATA to avoid unnecessary runs.
--
-- Environment naming: all object references use {{env_suffix}}
-- DCM resolves: DEV → _DEV, PROD → (empty)
-- ============================================================

-- Root task: orchestrates the full pipeline on a schedule.
-- Child tasks run only when their upstream stream has data.
CREATE OR REPLACE TASK SANDBOX{{env_suffix}}.TPCH.PIPELINE_ROOT_TASK
    WAREHOUSE = ANALYTICS_WH{{env_suffix}}
    SCHEDULE  = 'USING CRON 5 6 * * * UTC'
    COMMENT   = 'Root task — triggers the ingestion pipeline DAG'
AS
    SELECT 'Pipeline triggered at ' || CURRENT_TIMESTAMP();


-- Task 1: Validate and merge raw customers into the curated table.
-- Runs after root task, only if the stream has new rows.
CREATE OR REPLACE TASK SANDBOX{{env_suffix}}.TPCH.MERGE_CUSTOMERS_TASK
    WAREHOUSE = ANALYTICS_WH{{env_suffix}}
    COMMENT   = 'Upsert raw customers into SANDBOX{{env_suffix}}.TPCH.CUSTOMERS'
    AFTER     SANDBOX{{env_suffix}}.TPCH.PIPELINE_ROOT_TASK
    WHEN      SYSTEM$STREAM_HAS_DATA('SANDBOX{{env_suffix}}.TPCH_LANDING.CUSTOMERS_RAW_STREAM')
AS
    MERGE INTO SANDBOX{{env_suffix}}.TPCH.CUSTOMERS AS tgt
    USING (
        SELECT
            TRY_CAST(CUSTOMER_ID AS NUMBER)                     AS CUSTOMER_ID,
            TRIM(NAME)                                          AS NAME,
            LOWER(TRIM(EMAIL))                                  AS EMAIL,
            TRY_TO_TIMESTAMP_NTZ(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS') AS CREATED_AT
        FROM SANDBOX{{env_suffix}}.TPCH_LANDING.CUSTOMERS_RAW_STREAM
        WHERE METADATA$ACTION = 'INSERT'
          AND CUSTOMER_ID IS NOT NULL
    ) AS src
    ON tgt.CUSTOMER_ID = src.CUSTOMER_ID
    WHEN MATCHED THEN UPDATE SET
        tgt.NAME       = src.NAME,
        tgt.EMAIL      = src.EMAIL,
        tgt.CREATED_AT = src.CREATED_AT
    WHEN NOT MATCHED THEN INSERT
        (CUSTOMER_ID, NAME, EMAIL, CREATED_AT)
        VALUES (src.CUSTOMER_ID, src.NAME, src.EMAIL, src.CREATED_AT);


-- Task 2: Load raw orders into curated table (append-only stream).
CREATE OR REPLACE TASK SANDBOX{{env_suffix}}.TPCH.LOAD_ORDERS_TASK
    WAREHOUSE = ANALYTICS_WH{{env_suffix}}
    COMMENT   = 'Insert new orders from stream into SANDBOX{{env_suffix}}.TPCH.ORDERS'
    AFTER     SANDBOX{{env_suffix}}.TPCH.PIPELINE_ROOT_TASK
    WHEN      SYSTEM$STREAM_HAS_DATA('SANDBOX{{env_suffix}}.TPCH_LANDING.ORDERS_RAW_STREAM')
AS
    INSERT INTO SANDBOX{{env_suffix}}.TPCH.ORDERS
        (ORDER_ID, CUSTOMER_ID, ORDER_DATE, TOTAL_AMOUNT, STATUS)
    SELECT
        TRY_CAST(ORDER_ID     AS NUMBER)         AS ORDER_ID,
        TRY_CAST(CUSTOMER_ID  AS NUMBER)         AS CUSTOMER_ID,
        TRY_TO_DATE(ORDER_DATE, 'YYYY-MM-DD')    AS ORDER_DATE,
        TRY_CAST(TOTAL_AMOUNT AS NUMBER(12, 2))  AS TOTAL_AMOUNT,
        UPPER(TRIM(STATUS))                      AS STATUS
    FROM SANDBOX{{env_suffix}}.TPCH_LANDING.ORDERS_RAW_STREAM
    WHERE METADATA$ACTION = 'INSERT'
      AND ORDER_ID IS NOT NULL
      AND CUSTOMER_ID IS NOT NULL;


-- Task 3: Refresh the CUSTOMER_ORDER_SUMMARY view materialization
-- (runs after both merge and load tasks complete).
CREATE OR REPLACE TASK SANDBOX{{env_suffix}}.TPCH.REFRESH_SUMMARY_TASK
    WAREHOUSE = ANALYTICS_WH{{env_suffix}}
    COMMENT   = 'Placeholder for any post-load refresh logic (dynamic tables auto-refresh)'
    AFTER     SANDBOX{{env_suffix}}.TPCH.MERGE_CUSTOMERS_TASK,
              SANDBOX{{env_suffix}}.TPCH.LOAD_ORDERS_TASK
AS
    SELECT 'Summary refresh complete at ' || CURRENT_TIMESTAMP();


-- ============================================================
-- Enable the task DAG (tasks are SUSPENDED by default)
-- Run these after deploying:
-- ============================================================
--   ALTER TASK SANDBOX{{env_suffix}}.TPCH.REFRESH_SUMMARY_TASK RESUME;
--   ALTER TASK SANDBOX{{env_suffix}}.TPCH.LOAD_ORDERS_TASK RESUME;
--   ALTER TASK SANDBOX{{env_suffix}}.TPCH.MERGE_CUSTOMERS_TASK RESUME;
--   ALTER TASK SANDBOX{{env_suffix}}.TPCH.PIPELINE_ROOT_TASK RESUME;   -- Resume root last
