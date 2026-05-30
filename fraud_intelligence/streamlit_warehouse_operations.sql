-- ============================================================================
-- FRAUD INTELLIGENCE SOLUTION - WAREHOUSE RUNTIME DEPLOYMENT
-- ============================================================================
--
-- This file deploys the Streamlit app using WAREHOUSE RUNTIME (not container).
-- Warehouse runtime uses _snowflake.send_snow_api_request() for Cortex Agent
-- API calls — no EAI or compute pool required.
--
-- APP DETAILS:
--   Database: DEMO_DEV
--   Schema: FRAUD_INTELLIGENCE
--   App Name: FRAUD_INTELLIGENCE_SOLUTION
--   Warehouse: AGENT_DEMO_WH
--   Role: AGENT_DEMO_ROLE
--   Runtime: SYSTEM$WAREHOUSE_RUNTIME (default)
--   Stage: @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE
-- ============================================================================

USE ROLE AGENT_DEMO_ROLE;
USE WAREHOUSE AGENT_DEMO_WH;

-- ============================================================================
-- 1. CLEAN OLD FILES FROM STAGE
-- ============================================================================
REMOVE @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE/streamlit_app.py;
REMOVE @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE/styles.py;
REMOVE @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE/pyproject.toml;
REMOVE @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE/environment.yml;

-- ============================================================================
-- 2. COPY UPDATED FILES FROM WORKSPACE TO STAGE
-- ============================================================================
COPY FILES INTO @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE
  FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
  FILES=('streamlit_app.py');

COPY FILES INTO @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE
  FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
  FILES=('styles.py');

COPY FILES INTO @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE
  FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
  FILES=('environment.yml');

-- ============================================================================
-- 3. CREATE STREAMLIT OBJECT (WAREHOUSE RUNTIME)
--    No COMPUTE_POOL, no RUNTIME_NAME (defaults to SYSTEM$WAREHOUSE_RUNTIME),
--    no EXTERNAL_ACCESS_INTEGRATIONS needed.
-- ============================================================================
CREATE OR REPLACE STREAMLIT DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_SOLUTION
  FROM '@DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE'
  MAIN_FILE = 'streamlit_app.py'
  QUERY_WAREHOUSE = 'AGENT_DEMO_WH'
  TITLE = 'Fraud Intelligence Solution';

-- ============================================================================
-- 4. SET LIVE VERSION
-- ============================================================================
ALTER STREAMLIT DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_SOLUTION
  ADD LIVE VERSION FROM LAST;

-- ============================================================================
-- 5. VERIFY DEPLOYMENT
-- ============================================================================
DESCRIBE STREAMLIT DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_SOLUTION;
LIST @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE;

-- ============================================================================
-- 6. REDEPLOY CODE-ONLY UPDATES (for future changes, no recreate needed)
-- ============================================================================
-- After editing files in workspace, run these to push updates:
--
-- REMOVE @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE/streamlit_app.py;
-- REMOVE @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE/styles.py;
--
-- COPY FILES INTO @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE
--   FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
--   FILES=('streamlit_app.py');
--
-- COPY FILES INTO @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE
--   FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
--   FILES=('styles.py');
--
-- COPY FILES INTO 'snow://streamlit/DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_SOLUTION/versions/live/'
--   FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
--   FILES=('streamlit_app.py');
--
-- COPY FILES INTO 'snow://streamlit/DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_SOLUTION/versions/live/'
--   FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
--   FILES=('styles.py');
--
-- Then refresh browser (F5 / Cmd+R) on the app URL.
