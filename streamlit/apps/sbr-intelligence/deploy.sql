-- =============================================================================
-- SBR Intelligence Platform - Streamlit Deployment
-- =============================================================================

USE ROLE SBR_ANALYTICS_ROLE;
USE SCHEMA DEMO_DEV.SBR_ANALYTICS;

CREATE OR REPLACE STREAMLIT DEMO_DEV.SBR_ANALYTICS.SBR_INTELLIGENCE_PLATFORM
    ROOT_LOCATION = '@DEMO_DEV.SBR_ANALYTICS.SBR_STREAMLIT_STAGE'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = 'SBR_ANALYTICS_WH'
    TITLE = 'SBR Intelligence Platform';
