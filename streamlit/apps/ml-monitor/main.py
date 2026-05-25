import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parents[2]))

import streamlit as st
from shared.utils import get_session, fmt_number

st.set_page_config(page_title="ML Model Monitor", layout="wide")
st.title("ML Model Monitor")

session = get_session()

# ── Active models ────────────────────────────────────────────────────────────
st.header("Active Models")

active_df = session.sql("""
    SELECT
        MODEL_NAME,
        MODEL_VERSION,
        OWNER,
        RISK_TIER,
        STAGE,
        REGISTERED_AT
    FROM ML_PROD.MLOPS.V_ACTIVE_MODELS
    ORDER BY REGISTERED_AT DESC
""").to_pandas()

if active_df.empty:
    st.info("No active models found in ML_PROD.MLOPS. Deploy your first model to see it here.")
else:
    st.metric("Active Models", fmt_number(len(active_df)))
    st.dataframe(active_df, use_container_width=True)

# ── 7-day health summary ─────────────────────────────────────────────────────
st.header("Model Health (Last 7 Days)")

health_df = session.sql("""
    SELECT
        EVENT_DAY,
        MODEL_NAME,
        MODEL_VERSION,
        REQUEST_COUNT,
        ROUND(AVG_LATENCY_MS, 1)  AS AVG_LATENCY_MS,
        ROUND(P95_LATENCY_MS, 1)  AS P95_LATENCY_MS,
        ROUND(AVG_QUALITY_SIGNAL, 3) AS AVG_QUALITY_SIGNAL,
        ROUND(AVG_DRIFT_SCORE, 3)    AS AVG_DRIFT_SCORE
    FROM ML_PROD.MLOPS.V_MODEL_HEALTH_DAILY
    WHERE EVENT_DAY >= CURRENT_DATE - 7
    ORDER BY EVENT_DAY DESC, MODEL_NAME
""").to_pandas()

if health_df.empty:
    st.info("No prediction log data in the last 7 days.")
else:
    st.dataframe(health_df, use_container_width=True)

# ── Recent deployment events ─────────────────────────────────────────────────
st.header("Recent Deployment Events")

events_df = session.sql("""
    SELECT
        MODEL_NAME,
        MODEL_VERSION,
        ENVIRONMENT,
        EVENT_TYPE,
        EVENT_STATUS,
        APPROVED_BY,
        CREATED_AT
    FROM ML_PROD.MLOPS.MODEL_DEPLOYMENT_EVENTS
    ORDER BY CREATED_AT DESC
    LIMIT 20
""").to_pandas()

if events_df.empty:
    st.info("No deployment events recorded yet.")
else:
    st.dataframe(events_df, use_container_width=True)
