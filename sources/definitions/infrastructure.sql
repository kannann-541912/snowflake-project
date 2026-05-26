-- ============================================================
-- DEFINE Infrastructure Definitions (DCM Managed)
-- Warehouses and Schemas for RETAIL_CATEGORY_ANALYTICS_AGENT
-- ============================================================

DEFINE WAREHOUSE RETAIL_CATEGORY_ANALYTICS_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Dedicated compute warehouse for the Retail Category Analytics Agent. Used by Streamlit, Snowpark, and scheduled Tasks.';

DEFINE SCHEMA DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT
    COMMENT = 'Schema for the Retail Category Analytics Agent. Contains Bronze/Silver/Gold medallion tables, Snowpark stored procedures, Streamlit app, and OpenFlow ingestion pipeline for competitor pricing intelligence.';
