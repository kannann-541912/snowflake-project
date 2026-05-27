-- ============================================================================
-- FRAUD INTELLIGENCE PLATFORM - STREAMLIT APP OPERATIONS GUIDE
-- ============================================================================
-- 
-- ERROR REFERENCE:
-- {"level":"ERROR","message":"Application files download failed: failed to process 
--  Streamlit metadata\ndescribe output missing stage locations",
--  "source":"manager","timestamp":"2026-05-27T13:04:06Z"}
--
-- ROOT CAUSE: The live_version_location_uri was empty in the Streamlit object
-- metadata. The container manager could not determine where to download app
-- files from when starting the app.
--
-- APP DETAILS:
--   Database: DEMO_DEV
--   Schema: FRAUD_INTELLIGENCE
--   App Name: FRAUD_INTELLIGENCE_PLATFORM
--   Compute Pool: AGENT_DEMO
--   Runtime: SYSTEM$ST_CONTAINER_RUNTIME_PY3_11
--   Stage: @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE
-- ============================================================================

USE ROLE AGENT_DEMO_ROLE;
USE WAREHOUSE AGENT_DEMO_WH;

-- ============================================================================
-- 1. BEFORE RUNNING DEMO: Resume the compute pool
-- ============================================================================
ALTER COMPUTE POOL AGENT_DEMO RESUME;

-- ============================================================================
-- 2. AFTER DEMO: Suspend compute pool to save credits
--    (Container runtime stays alive for up to 3 days after last viewer,
--     consuming credits the entire time. Manually suspend to stop billing.)
-- ============================================================================
ALTER COMPUTE POOL AGENT_DEMO SUSPEND;

-- ============================================================================
-- 3. FIX: If the "missing stage locations" error occurs again
--    (Recreates the Streamlit object and sets the live version)
-- ============================================================================
CREATE OR REPLACE STREAMLIT DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_PLATFORM
  FROM '@DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE'
  MAIN_FILE = 'streamlit_app.py'
  QUERY_WAREHOUSE = 'AGENT_DEMO_WH'
  TITLE = 'Fraud Intelligence Platform'
  EXTERNAL_ACCESS_INTEGRATIONS = (AGENT_DEMO_API_EAI)
  COMPUTE_POOL = AGENT_DEMO
  RUNTIME_NAME = 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11';

ALTER STREAMLIT DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_PLATFORM
  ADD LIVE VERSION FROM LAST;

-- ============================================================================
-- 4. VERIFY: Check that live_version_location_uri is populated
--    (Should show: snow://streamlit/.../versions/live/)
-- ============================================================================
DESCRIBE STREAMLIT DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_PLATFORM;

-- ============================================================================
-- 5. DIAGNOSTICS: Check compute pool and app status
-- ============================================================================
SHOW COMPUTE POOLS LIKE 'AGENT_DEMO';
SHOW STREAMLITS IN SCHEMA DEMO_DEV.FRAUD_INTELLIGENCE;

-- ============================================================================
-- 6. VERIFY STAGE FILES: Confirm app files exist
-- ============================================================================
LIST @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE;

-- ============================================================================
-- 7. DEPLOY UPDATED CODE (after editing files in workspace)
-- ============================================================================
--
-- HOW CHANGED FILES ARE PICKED UP:
-- - Container runtime reads from live_version_location_uri
-- - When you COPY FILES INTO the live URI, files are updated immediately
-- - Current viewers see changes on next interaction (widget click, rerun)
-- - To force immediate reload: refresh the browser tab (F5 / Cmd+R)
-- - If compute pool is suspended: new code loads automatically on next resume
-- - No ALTER STREAMLIT or restart is required for code-only changes
--
-- ============================================================================

-- 7a. Remove old files from source stage (backup cleanup)
REMOVE @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE/streamlit_app.py;
REMOVE @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE/styles.py;

-- 7b. Copy updated files from workspace to source stage (backup/source of truth)
COPY FILES INTO @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE
  FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
  FILES=('streamlit_app.py');

COPY FILES INTO @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE
  FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
  FILES=('styles.py');

-- 7c. Copy updated files to live version URI (updates running app immediately)
--     No cleanup needed on live URI — COPY FILES overwrites in place
COPY FILES INTO 'snow://streamlit/DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_PLATFORM/versions/live/'
  FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
  FILES=('streamlit_app.py');

COPY FILES INTO 'snow://streamlit/DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_PLATFORM/versions/live/'
  FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live/fraud_intelligence/streamlit/'
  FILES=('styles.py');

-- 7d. Verify stage files are updated (check last_modified timestamps)
LIST @DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_INTELLIGENCE_APP_STAGE;

-- 7e. REFRESH APP: Open the Streamlit app URL and refresh browser (F5 / Cmd+R)
