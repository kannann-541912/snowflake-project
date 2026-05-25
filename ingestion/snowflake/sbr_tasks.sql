-- =============================================================================
-- SBR Intelligence Platform - Pipeline Ingestion Tasks
-- Snowflake Task definitions for automated DAG execution
-- =============================================================================

USE ROLE SBR_ANALYTICS_ROLE;
USE SCHEMA DEMO_DEV.SBR_ANALYTICS;

-- Root task: Daily labor ingestion
CREATE OR REPLACE TASK SBR_DAILY_INGEST
    WAREHOUSE = SBR_ANALYTICS_WH
    SCHEDULE = 'USING CRON 0 6 * * * America/Edmonton'
    COMMENT = 'Daily ingestion of vendor labor CSV files from SBR_SOURCE_STAGE'
AS
    COPY INTO BRONZE_LABOR (EMP_ID, WORK_DATE, HOURS, RATE, TOTAL_PAY, FILE_NAME, BATCH_ID, LOAD_TS, _SOURCE_FILE, _INGESTED_AT)
    FROM (
        SELECT $1, $2, $3, $4, $5,
               METADATA$FILENAME,
               'BATCH_' || TO_VARCHAR(CURRENT_DATE(), 'YYYYMMDD'),
               CURRENT_TIMESTAMP(),
               METADATA$FILENAME,
               CURRENT_TIMESTAMP()
        FROM @SBR_SOURCE_STAGE
    )
    FILE_FORMAT = CSV_FMT
    ON_ERROR = 'CONTINUE';

-- Schema validation task
CREATE OR REPLACE TASK SBR_SCHEMA_VALIDATE
    WAREHOUSE = SBR_ANALYTICS_WH
    AFTER SBR_DAILY_INGEST
    COMMENT = 'Validates vendor file schemas against registry'
AS
    CALL SBR_DETECT_SCHEMA_GAPS('V001', 'latest.csv', '[]');

-- Silver transformation task
CREATE OR REPLACE TASK SBR_SILVER_TRANSFORM
    WAREHOUSE = SBR_ANALYTICS_WH
    AFTER SBR_SCHEMA_VALIDATE
    COMMENT = 'Transforms bronze to silver with type casting and validation'
AS
    INSERT INTO SILVER_LABOR (EMP_ID, WORK_DATE, HOURS_WORKED, PAY_RATE, PAYROLL_AMOUNT, FILE_NAME, BATCH_ID, LOAD_TS, DATA_QUALITY_STATUS)
    SELECT
        EMP_ID,
        TRY_TO_DATE(WORK_DATE),
        TRY_TO_NUMBER(HOURS, 10, 2),
        TRY_TO_NUMBER(RATE, 10, 2),
        TRY_TO_NUMBER(TOTAL_PAY, 12, 2),
        FILE_NAME,
        BATCH_ID,
        LOAD_TS,
        CASE WHEN TRY_TO_DATE(WORK_DATE) IS NULL OR TRY_TO_NUMBER(HOURS, 10, 2) IS NULL THEN 'FAIL' ELSE 'PASS' END
    FROM BRONZE_LABOR
    WHERE BATCH_ID = 'BATCH_' || TO_VARCHAR(CURRENT_DATE(), 'YYYYMMDD');

-- Gold fact build task
CREATE OR REPLACE TASK SBR_GOLD_BUILD
    WAREHOUSE = SBR_ANALYTICS_WH
    AFTER SBR_SILVER_TRANSFORM
    COMMENT = 'Builds gold fact table with variance calculations'
AS
    INSERT INTO GOLD_FACT_LABOR (EMP_ID, WORK_DATE, HOURS_WORKED, PAY_RATE, PAYROLL_AMOUNT, EXPECTED_PAY, VARIANCE, BATCH_ID, VENDOR_ID)
    SELECT
        s.EMP_ID,
        s.WORK_DATE,
        s.HOURS_WORKED,
        s.PAY_RATE,
        s.PAYROLL_AMOUNT,
        s.HOURS_WORKED * s.PAY_RATE AS EXPECTED_PAY,
        s.PAYROLL_AMOUNT - (s.HOURS_WORKED * s.PAY_RATE) AS VARIANCE,
        s.BATCH_ID,
        COALESCE(v.VENDOR_ID, 'UNKNOWN')
    FROM SILVER_LABOR s
    LEFT JOIN GOLD_DIM_VENDOR v ON 1=1
    WHERE s.DATA_QUALITY_STATUS = 'PASS'
      AND s.BATCH_ID = 'BATCH_' || TO_VARCHAR(CURRENT_DATE(), 'YYYYMMDD');

-- Audit metrics task
CREATE OR REPLACE TASK SBR_AUDIT_CAPTURE
    WAREHOUSE = SBR_ANALYTICS_WH
    AFTER SBR_GOLD_BUILD
    COMMENT = 'Captures audit metrics after pipeline completion'
AS
    CALL SBR_AUDIT_METRICS_AGENT();
