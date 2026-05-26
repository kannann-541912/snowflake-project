-- ============================================================
-- Secrets
-- Schema: DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT
-- Never store actual secret values in code — use placeholders.
-- Actual values are set via Snowsight or CI secrets injection.
-- ============================================================

CREATE OR REPLACE SECRET DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.SERPAPI_ACCESS_CREDENTIALS
    TYPE = GENERIC_STRING
    SECRET_STRING = ''     -- PLACEHOLDER — set actual value in Snowsight
    COMMENT = 'SerpAPI authentication key for competitor price scraping. Get free key at serpapi.com. Rotate by updating SECRET_STRING if key is compromised.';

GRANT USAGE ON SECRET DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.SERPAPI_ACCESS_CREDENTIALS
    TO ROLE RETAIL_CATEGORY_ANALYTICS_ROLE;
