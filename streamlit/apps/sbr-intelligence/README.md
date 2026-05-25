# SBR Intelligence Platform - Streamlit App
# 
# The full streamlit_app.py is deployed at:
#   @DEMO_DEV.SBR_ANALYTICS.SBR_STREAMLIT_STAGE/streamlit_app.py
#
# To retrieve the latest deployed version:
#   SELECT $1 FROM @DEMO_DEV.SBR_ANALYTICS.SBR_STREAMLIT_STAGE/streamlit_app.py
#     (FILE_FORMAT => 'DEMO_DEV.SBR_ANALYTICS.RAW_TEXT');
#
# App Features:
# - 5 Tabs: Overview, Vendors, Payroll Exceptions, Investigation Management, Governance
# - 7 KPIs: Payroll, Expected, Variance, Overpaid, Underpaid, Variance Alerts, Open Cases
# - Altair charts with cyan (#01b8fb) and pink (#E040FB) color scheme
# - Ask SBR Agent using SBR_ANALYTICS_AGENT (Cortex Agent)
# - Dark theme via shared styles.py + config.toml
# - Mastech Digital logo from @DEMO_DEV.PUBLIC.SHARED_ASSETS
# - Sidebar: Year, Date Range, Variance Threshold, Vendors, Employees filters
#
# Dependencies:
#   streamlit, pandas, altair, json, sys, base64, snowflake.snowpark
#
# Deployment:
#   CREATE OR REPLACE STREAMLIT DEMO_DEV.SBR_ANALYTICS.SBR_INTELLIGENCE_PLATFORM
#       ROOT_LOCATION = '@DEMO_DEV.SBR_ANALYTICS.SBR_STREAMLIT_STAGE'
#       MAIN_FILE = 'streamlit_app.py'
#       QUERY_WAREHOUSE = 'SBR_ANALYTICS_WH'
#       TITLE = 'SBR Intelligence Platform';

# NOTE: Full source code is in the deployed stage. 
# Run the SQL above to extract it for version control.
