-- ============================================================
-- DEFINE Stage & File Format Definitions (DCM Managed)
-- Schema: DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT
-- No FILE FORMAT objects exist in this schema.
-- ============================================================

DEFINE STAGE DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.RAW_DATA_UPLOAD_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Internal Snowflake stage for raw data file uploads. Used by OpenFlow to load CSV files into Bronze layer tables. Files are organized in subfolders by data type.';

DEFINE STAGE DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.CATEGORY_INTELLIGENCE_APP_STAGE
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Streamlit app files for Category Intelligence Platform';
