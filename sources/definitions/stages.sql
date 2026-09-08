-- ============================================================
-- External Stages — Landing Zone
-- All names use {{env_suffix}} for environment-aware naming.
-- Replace the S3 URL and storage integration
-- with your actual values before deploying.
-- ============================================================

-- Landing schema
DEFINE SCHEMA SANDBOX{{env_suffix}}.TPCH_LANDING
    COMMENT = 'Raw landing zone for external data files';

-- File format: CSV with header
DEFINE FILE FORMAT SANDBOX{{env_suffix}}.TPCH_LANDING.CSV_FORMAT
    TYPE = CSV
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    DATE_FORMAT = 'YYYY-MM-DD'
    TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS'
    NULL_IF = ('', 'NULL', 'null')
    EMPTY_FIELD_AS_NULL = TRUE;

-- File format: JSON (for API payloads)
DEFINE FILE FORMAT SANDBOX{{env_suffix}}.TPCH_LANDING.JSON_FORMAT
    TYPE = JSON
    STRIP_OUTER_ARRAY = TRUE;

-- External stage: Customers source (S3)
-- Requires a storage integration named TPCH_S3_INTEGRATION to be created first.
DEFINE STAGE SANDBOX{{env_suffix}}.TPCH_LANDING.CUSTOMERS_STAGE
    URL = 's3://your-data-bucket/customers/'
    STORAGE_INTEGRATION = TPCH_S3_INTEGRATION
    FILE_FORMAT = SANDBOX{{env_suffix}}.TPCH_LANDING.CSV_FORMAT
    COMMENT = 'Raw customer files from S3';

-- External stage: Orders source (S3)
DEFINE STAGE SANDBOX{{env_suffix}}.TPCH_LANDING.ORDERS_STAGE
    URL = 's3://your-data-bucket/orders/'
    STORAGE_INTEGRATION = TPCH_S3_INTEGRATION
    FILE_FORMAT = SANDBOX{{env_suffix}}.TPCH_LANDING.CSV_FORMAT
    COMMENT = 'Raw order files from S3';

-- Internal stage: For Snowpark-generated files
DEFINE STAGE SANDBOX{{env_suffix}}.TPCH_LANDING.SNOWPARK_OUTPUT_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Internal stage for Snowpark transform outputs';
