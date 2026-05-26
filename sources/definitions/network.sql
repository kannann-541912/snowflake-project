-- ============================================================
-- Network Rules & External Access Integrations
-- Schema: DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT
-- Requires SYSADMIN/ACCOUNTADMIN. Deployed via CI with elevated role.
-- ============================================================

CREATE OR REPLACE NETWORK RULE DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.SERPAPI_NETWORK_RULE
    TYPE = HOST_PORT
    MODE = EGRESS
    VALUE_LIST = ('serpapi.com')
    COMMENT = 'Allows egress to SerpAPI for competitor price scraping via Google Shopping API';

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION SERPAPI_ACCESS_INTEGRATION
    ALLOWED_NETWORK_RULES = (DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.SERPAPI_NETWORK_RULE)
    ENABLED = TRUE
    COMMENT = 'External access integration for SerpAPI competitor pricing ingestion';

GRANT USAGE ON INTEGRATION SERPAPI_ACCESS_INTEGRATION
    TO ROLE RETAIL_CATEGORY_ANALYTICS_ROLE;
