-- DEPLOYMENT SEQUENCE — run statements in order
-- All statements can be run in Snowsight worksheet with SYSADMIN role

-- Statement 1: Clean existing objects
DROP STREAMLIT IF EXISTS ADMIN_DB.OPS.FINOPS_VALUE_INTELLIGENCE;
DROP STAGE IF EXISTS ADMIN_DB.OPS.FINOPS_DEMO_STAGE;

-- Statement 2: Create stage
CREATE STAGE IF NOT EXISTS ADMIN_DB.OPS.FINOPS_DEMO_STAGE
  DIRECTORY = (ENABLE = TRUE)
  COMMENT = 'Stage for FinOps Value Intelligence app';

-- Statement 3: Copy app files from workspace to stage
-- Copies ONLY the two specified files, not the entire workspace
REMOVE @ADMIN_DB.OPS.FINOPS_DEMO_STAGE;

COPY FILES INTO @ADMIN_DB.OPS.FINOPS_DEMO_STAGE
FROM 'snow://workspace/USER$.PUBLIC."FinOps_PA"/versions/live/'
FILES = ('06_streamlit_app.py', 'styles.py', 'environment.yml');

-- Statement 3b: Copy config.toml into .streamlit subfolder
COPY FILES INTO @ADMIN_DB.OPS.FINOPS_DEMO_STAGE/.streamlit/
FROM 'snow://workspace/USER$.PUBLIC."FinOps_PA"/versions/live/.streamlit'
FILES = ('config.toml');

-- Statement 4: Verify upload before proceeding
-- Confirm 06_streamlit_app.py, styles.py, environment.yml, and .streamlit/config.toml appear
LIST @ADMIN_DB.OPS.FINOPS_DEMO_STAGE;

-- Statement 5: Create Streamlit app (warehouse runtime)
CREATE OR REPLACE STREAMLIT ADMIN_DB.OPS.FINOPS_VALUE_INTELLIGENCE
  FROM '@ADMIN_DB.OPS.FINOPS_DEMO_STAGE'
  MAIN_FILE = '06_streamlit_app.py'
  QUERY_WAREHOUSE = AGENT_DEMO_WH
  TITLE = 'FinOps Value Intelligence'
  COMMENT = 'FinOps cost to value demo';

-- Statement 6: Make it live
ALTER STREAMLIT ADMIN_DB.OPS.FINOPS_VALUE_INTELLIGENCE ADD LIVE VERSION FROM LAST;

-- Statement 7: Grant access
GRANT USAGE ON STREAMLIT ADMIN_DB.OPS.FINOPS_VALUE_INTELLIGENCE TO ROLE SYSADMIN;

-- Statement 8: Confirm app created
SHOW STREAMLITS IN SCHEMA ADMIN_DB.OPS;

-- ROOT_LOCATION is legacy — use FROM instead
-- MAIN_FILE must NOT start with / when using FROM syntax
-- environment.yml must be in the same stage root for plotly to resolve
-- Access via: Projects > Streamlit > FINOPS_VALUE_INTELLIGENCE
