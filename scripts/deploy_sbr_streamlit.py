"""
SBR Intelligence Platform - Deploy Streamlit App Script
Deploys the SBR Intelligence Platform Streamlit app from stage.
"""

DEPLOY_SQL = """
CREATE OR REPLACE STREAMLIT DEMO_DEV.SBR_ANALYTICS.SBR_INTELLIGENCE_PLATFORM
    ROOT_LOCATION = '@DEMO_DEV.SBR_ANALYTICS.SBR_STREAMLIT_STAGE'
    MAIN_FILE = 'streamlit_app.py'
    QUERY_WAREHOUSE = 'SBR_ANALYTICS_WH'
    TITLE = 'SBR Intelligence Platform';
"""

if __name__ == "__main__":
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
    session.sql(DEPLOY_SQL).collect()
    print("SBR Intelligence Platform Streamlit app deployed successfully.")
    print("Access at: Snowsight > Streamlit > SBR Intelligence Platform")
