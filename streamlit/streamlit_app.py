"""
Category Intelligence
Snowflake-Native Streamlit Application

Tabs: Category | Promotions & Campaigns | Customer Loyalty | Returns & Margin Impact
Sidebar: Analysis Views
Agent Chat at top with business heading

All data from DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT schema.
Runs entirely inside Snowflake — no external server.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime

# Force theme primaryColor before anything renders
from streamlit import config as _stconfig
_stconfig.set_option("theme.primaryColor", "#f97316")
_stconfig.set_option("theme.backgroundColor", "#030c25")
_stconfig.set_option("theme.secondaryBackgroundColor", "#0d558b")
_stconfig.set_option("theme.textColor", "#ecf6fd")

import snowflake.snowpark.context as snowpark_ctx
from styles import apply_theme, app_header, section_card, status_banner, badge

# ──────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Category Intelligence",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ──────────────────────────────────────────────────────────────────
# APPLY SHARED THEME + APP-SPECIFIC STYLES
# ──────────────────────────────────────────────────────────────────
apply_theme()

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

  /* Override Streamlit CSS variables at root — forces blue everywhere */
  :root {
    --primary-color: #f97316 !important;
    --background-color: #030c25 !important;
    --secondary-background-color: #0d558b !important;
    --text-color: #ecf6fd !important;
  }
  .stApp {
    --primary-color: #f97316 !important;
  }

  * { font-family: 'DM Sans', sans-serif !important; }

  /* Hide "View fullscreen" and data table toggle on charts */
  [data-testid="StyledFullScreenButton"],
  [data-testid="stElementToolbar"] {
    display: none !important;
  }



  .block-container { padding-top: 0rem !important; padding-bottom: 0.5rem !important; padding-left: 1rem !important; padding-right: 1rem !important; }

  /* Hide default Streamlit header space */
  header[data-testid="stHeader"] { display: none !important; }
  .stApp > header { display: none !important; }
  [data-testid="stToolbar"] { display: none !important; }

  /* Sidebar — compact buttons */
  [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.3rem; }
  [data-testid="stSidebar"] .stButton button { padding: 0.4rem 0.8rem; font-size: 0.82rem; }

  /* KPI card styling */
  .kpi-card {
    background: #0a1a3a; border: 1px solid #1a3a5c;
    border-radius: 8px; padding: 8px 14px;
  }
  .kpi-card .kpi-label {
    font-size: 0.68rem; font-weight: 700; color: #8ec9f5;
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 1px;
  }
  .kpi-card .kpi-value {
    font-size: 1.5rem; font-weight: 700; color: #ecf6fd; margin: 0;
  }
  .kpi-card .kpi-delta { font-size: 0.7rem; margin-top: 1px; }
  .kpi-delta-up { color: #4ade80; }
  .kpi-delta-down { color: #fbbf24; }

  /* Governance footer */
  .governance-bar {
    background: #0a1a3a; border: 1px solid #1a3a5c;
    border-radius: 6px; padding: 10px 14px; margin-top: 16px;
  }
  .governance-bar .gov-title { color: #01b8fb; font-weight: 700; font-size: 0.78rem; }

  /* Agent answer box */
  .agent-answer-box {
    background: #0a1a3a; border-left: 4px solid #01b8fb;
    padding: 10px 14px; border-radius: 0 8px 8px 0;
    margin: 6px 0; font-size: 0.85rem; color: #ecf6fd; line-height: 1.4;
  }

  /* Section label */
  .section-label {
    font-size: 0.72rem; font-weight: 700; color: #8ec9f5;
    text-transform: uppercase; letter-spacing: 0.07em; margin: 6px 0 4px 0;
  }

  /* Suggested question chips */
  .suggestion-chips { display: flex; gap: 8px; flex-wrap: wrap; margin: 6px 0 10px 0; }
  .suggestion-chips button {
    background: #0a1a3a !important; border: 1px solid #1a3a5c !important;
    border-radius: 16px !important; padding: 4px 14px !important;
    font-size: 0.78rem !important; color: #8ec9f5 !important;
    cursor: pointer !important; transition: all 0.2s !important;
  }
  .suggestion-chips button:hover {
    border-color: #01b8fb !important; color: #01b8fb !important;
    background: #0d558b !important;
  }

  /* Suggested question buttons */
  [data-testid="stHorizontalBlock"]:has(button[key*="suggestion"]) button,
  button[key*="suggestion"] {
    background: #0d558b !important; border: 1px solid #01b8fb !important;
    border-radius: 8px !important; color: #ecf6fd !important;
    font-size: 0.74rem !important; padding: 6px 10px !important;
  }
  [data-testid="stHorizontalBlock"]:has(button[key*="suggestion"]) button:hover,
  [data-testid="stHorizontalBlock"]:has(button[key*="suggestion"]) button:focus,
  [data-testid="stHorizontalBlock"]:has(button[key*="suggestion"]) button:active,
  button[key*="suggestion"]:hover,
  button[key*="suggestion"]:focus,
  button[key*="suggestion"]:active {
    border-color: #01b8fb !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(1,184,251,0.3) !important;
    color: #ffffff !important;
    background: #0a1a3a !important;
  }

  /* Rectangular tabs with curved edges */
  button[data-baseweb="tab"] {
    background: #0a1a3a !important; border: 1px solid #1a3a5c !important;
    border-radius: 8px !important; padding: 8px 20px !important;
    font-size: 0.8rem !important; color: #ecf6fd !important;
    font-weight: 700 !important; margin-right: 6px !important;
  }
  button[data-baseweb="tab"][aria-selected="true"] {
    background: #0d558b !important; border-color: #01b8fb !important;
    color: #01b8fb !important; border-width: 2px !important;
  }
  button[data-baseweb="tab"]:hover {
    border-color: #01b8fb !important; color: #ffffff !important;
  }
  button[data-baseweb="tab"]:focus,
  button[data-baseweb="tab"]:active {
    border-color: #01b8fb !important; color: #01b8fb !important;
    outline: none !important; box-shadow: none !important;
  }
  div[data-baseweb="tab-list"] {
    gap: 12px !important; border-bottom: none !important; width: 100% !important; display: flex !important;
  }
  div[data-baseweb="tab-list"] button[data-baseweb="tab"] {
    flex: 1 !important;
  }
  [data-testid="stTabs"] [role="tablist"] {
    width: 100% !important; display: flex !important; gap: 12px !important;
  }
  [data-testid="stTabs"] [role="tablist"] button {
    flex: 1 !important;
  }
  div[data-baseweb="tab-highlight"] { display: none !important; background: transparent !important; }
  div[data-baseweb="tab-border"] { display: none !important; background: transparent !important; }

  /* Catch-all for Streamlit tabs — any version */
  [data-testid="stTabs"] button[aria-selected="true"] {
    background: #0d558b !important; border-color: #01b8fb !important;
    color: #01b8fb !important; border: 2px solid #01b8fb !important;
  }
  [data-testid="stTabs"] button {
    background: #0a1a3a !important; border: 1px solid #1a3a5c !important;
    border-radius: 8px !important; color: #ecf6fd !important;
    font-weight: 700 !important;
  }
  [data-testid="stTabs"] button:hover {
    border-color: #01b8fb !important; color: #ffffff !important;
  }
  [data-testid="stTabs"] button:focus,
  [data-testid="stTabs"] button:active {
    outline: none !important; box-shadow: none !important;
    border-color: #01b8fb !important; color: #01b8fb !important;
  }
  /* Hide the colored underline/highlight bar */
  [data-testid="stTabs"] [role="tablist"]::after,
  [data-testid="stTabs"] [role="tablist"] > div:last-child {
    background: transparent !important; display: none !important;
  }

  /* Override Streamlit's hardcoded rgb(255,75,75) red on selected tabs */
  [data-testid="stTabs"] button[aria-selected="true"][class*="css-"] {
    background-color: #0d558b !important;
    border-color: #01b8fb !important;
    color: #01b8fb !important;
    border: 2px solid #01b8fb !important;
    border-radius: 8px !important;
  }
  /* All tab buttons — override any css- class styling */
  [role="tablist"] button[class*="css-"] {
    background-color: #0a1a3a !important;
    border: 1px solid #1a3a5c !important;
    border-radius: 8px !important;
    color: #ecf6fd !important;
    font-weight: 700 !important;
  }
  [role="tablist"] button[class*="css-"][aria-selected="true"] {
    background-color: #0d558b !important;
    border: 2px solid #01b8fb !important;
    color: #01b8fb !important;
  }
  [role="tablist"] button[class*="css-"]:hover {
    border-color: #01b8fb !important;
    color: #ffffff !important;
  }
  div[data-baseweb="tab-panel"] { box-shadow: none !important; border: none !important; padding: 4px 0 0 0 !important; }
  [data-testid="stTabs"] { box-shadow: none !important; border: none !important; }
  [data-testid="stTabs"] > div { box-shadow: none !important; }
  [data-testid="stTabContent"] { box-shadow: none !important; border: none !important; overflow: visible !important; }

  /* Compact filters */
  [data-testid="stSelectbox"], [data-testid="stDateInput"] { margin-bottom: -10px !important; }
  [data-testid="stSelectbox"] label, [data-testid="stDateInput"] label { font-size: 0.68rem !important; margin-bottom: 0 !important; }
  [data-testid="stSelectbox"] > div > div, [data-testid="stDateInput"] > div > div { padding: 2px 8px !important; min-height: 32px !important; }



  /* Primary button override (active nav tabs) */
  [data-testid="stButton"] button[kind="primary"],
  [data-testid="stButton"] button[data-testid="baseButton-primary"] {
    background: linear-gradient(90deg, #01b8fb, #0d558b) !important;
    color: #ffffff !important;
    border: 1px solid #01b8fb !important;
  }
  /* Secondary button override (inactive nav tabs) */
  [data-testid="stButton"] button[kind="secondary"],
  [data-testid="stButton"] button[data-testid="baseButton-secondary"] {
    background: #0a1a3a !important;
    color: #8ec9f5 !important;
    border: 1px solid #1a3a5c !important;
  }
  [data-testid="stButton"] button[kind="secondary"]:hover,
  [data-testid="stButton"] button[data-testid="baseButton-secondary"]:hover {
    border-color: #01b8fb !important;
    color: #01b8fb !important;
  }

  /* Global: kill all red hover/focus rings on buttons */
  [data-testid="stButton"] button:hover,
  [data-testid="stButton"] button:focus,
  [data-testid="stButton"] button:active,
  [data-testid="stButton"] button:focus-visible,
  [data-testid="stButton"] button:visited,
  .stButton button:hover,
  .stButton button:focus,
  .stButton button:active,
  .stButton button:focus-visible,
  .stButton button:visited {
    border-color: #01b8fb !important;
    outline: none !important;
    box-shadow: none !important;
    color: #ffffff !important;
    background-color: #0d558b !important;
  }
  /* Also catch the p/span inside buttons */
  [data-testid="stButton"] button:hover p,
  [data-testid="stButton"] button:focus p,
  [data-testid="stButton"] button:active p,
  [data-testid="stButton"] button:hover span,
  [data-testid="stButton"] button:focus span,
  [data-testid="stButton"] button:active span {
    color: #ffffff !important;
  }
  /* Nuke any red from Streamlit theming */
  [data-testid="stButton"] button:focus, [data-testid="stButton"] button:focus-visible {
    outline-color: #01b8fb !important;
  }
  /* Text input — no outline at all */
  [data-testid="stTextInput"] input,
  [data-testid="stTextInput"] input:focus,
  [data-testid="stTextInput"] input:focus-visible,
  [data-testid="stTextInput"] input:active,
  [data-testid="stTextInput"] > div,
  [data-testid="stTextInput"] > div:focus-within,
  [data-testid="stTextInput"] div[data-baseweb="input"],
  [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within,
  [data-testid="stTextInput"] div[data-baseweb="base-input"],
  [data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within {
    border: none !important;
    border-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
    background: #0a1a3a !important;
  }

  /* Override ALL red focus/active rings on inputs, selects, sliders */
  [data-baseweb="input"]:focus-within,
  [data-baseweb="select"]:focus-within,
  [data-baseweb="input"][aria-expanded="true"],
  [data-baseweb="select"][aria-expanded="true"] {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 1px #f97316 !important;
  }
  [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
    border: 1px solid #f97316 !important;
    box-shadow: 0 0 0 1px #f97316 !important;
    background: #0a1a3a !important;
  }
  [data-testid="stSelectbox"] div[data-baseweb="select"]:focus-within,
  [data-testid="stMultiSelect"] div[data-baseweb="select"]:focus-within {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 1px #f97316 !important;
  }
  /* Slider thumb and track — override red */
  [data-testid="stSlider"] [role="slider"],
  [data-testid="stSlider"] [role="slider"]:focus,
  [data-testid="stSlider"] [role="slider"]:active {
    background-color: #f97316 !important;
    border-color: #f97316 !important;
    box-shadow: none !important;
  }
  [data-testid="stSlider"] div[data-testid="stThumbValue"] {
    color: #f97316 !important;
  }
  [data-testid="stSlider"] [role="progressbar"],
  [data-testid="stSlider"] div[style*="background-color: rgb(255, 75, 75)"],
  [data-testid="stSlider"] div[style*="background-color: rgb(255,75,75)"] {
    background-color: #f97316 !important;
  }
  /* Number input focus */
  [data-testid="stNumberInput"] input:focus,
  [data-testid="stNumberInput"] input:active {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 1px #f97316 !important;
    outline: none !important;
  }
  /* Date input focus */
  [data-testid="stDateInput"] div[data-baseweb="input"]:focus-within {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 1px #f97316 !important;
  }
  /* Global: override Streamlit's red primary on all interactive elements */
  [data-testid="stButton"] button:focus,
  [data-testid="stButton"] button:focus-visible,
  [data-testid="stTextInput"] input:focus,
  [data-testid="stSelectbox"] div:focus-within {
    outline-color: #f97316 !important;
  }

  /* Expander header/icon color */
  [data-testid="stExpander"] summary,
  [data-testid="stExpander"] summary:hover {
    color: #f97316 !important;
  }
  [data-testid="stExpander"] summary svg {
    fill: #f97316 !important;
    color: #f97316 !important;
  }
  [data-testid="stExpander"] {
    border-color: #f97316 !important;
  }

  /* Slider — aggressive override of all red/primary colors */
  [data-testid="stSlider"] div[role="slider"],
  [data-testid="stSlider"] div[role="slider"]:focus,
  [data-testid="stSlider"] div[role="slider"]:active {
    background-color: #f97316 !important;
    border-color: #f97316 !important;
  }
  [data-testid="stSlider"] div[role="slider"]:focus {
    box-shadow: 0 0 0 2px rgba(249,115,22,0.4) !important;
  }
  /* Slider filled track — target the inner colored bar */
  [data-testid="stSlider"] div[data-baseweb="slider"] div[role="progressbar"] {
    background-color: #f97316 !important;
  }
  [data-testid="stSlider"] div[data-baseweb="slider"] div[role="progressbar"] > div {
    background-color: #f97316 !important;
  }
  /* Override any div inside slider that has inline background-color */
  [data-testid="stSlider"] div[data-baseweb="slider"] > div > div > div {
    background-color: #f97316 !important;
  }
  [data-testid="stSlider"] div[data-baseweb="slider"] > div > div > div > div {
    background-color: transparent !important;
  }
  [data-testid="stSlider"] div[data-baseweb="slider"] > div > div > div > div:first-child {
    background-color: #f97316 !important;
  }
  /* Thumb value text */
  [data-testid="stSlider"] div[data-testid="stThumbValue"],
  [data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stThumbValue"] {
    color: #f97316 !important;
  }
  /* Slider current value display */
  [data-testid="stSlider"] div[data-baseweb="slider"] div[aria-valuenow] {
    background-color: #f97316 !important;
  }
  /* Checkbox/radio/toggle override */
  [data-testid="stCheckbox"] input:checked + div,
  input[type="checkbox"]:checked {
    background-color: #f97316 !important;
    border-color: #f97316 !important;
  }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────
SCHEMA = "DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT"
AGENT_NAME = "DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.RETAIL_CATEGORY_ANALYTICS_AGENT"

# ──────────────────────────────────────────────────────────────────
# SNOWFLAKE SESSION
# ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_session():
    return snowpark_ctx.get_active_session()


def run_sql(sql: str) -> pd.DataFrame:
    try:
        return get_session().sql(sql).to_pandas()
    except Exception as e:
        return pd.DataFrame({"_error": [str(e)]})


def has_error(df: pd.DataFrame) -> bool:
    return "_error" in df.columns or df.empty


def render_table(df: pd.DataFrame, max_height: str = "300px"):
    html = df.to_html(index=False, classes="styled-table", border=0, escape=True)
    st.markdown(f"""
    <div style="max-height:{max_height};overflow-y:auto;border:1px solid #1a3a5c;border-radius:8px;">
    <style>
    .styled-table {{width:100%;border-collapse:collapse;font-size:0.76rem;color:#ecf6fd;}}
    .styled-table thead tr {{background:#0d558b;position:sticky;top:0;z-index:1;}}
    .styled-table th {{padding:8px 10px;text-align:left;font-weight:700;color:#ecf6fd;border-bottom:1px solid #1a3a5c;font-size:0.7rem;text-transform:uppercase;letter-spacing:0.03em;}}
    .styled-table td {{padding:6px 10px;border-bottom:1px solid rgba(26,58,92,0.5);}}
    .styled-table tbody tr:hover {{background:rgba(1,184,251,0.06);}}
    .styled-table tbody tr:nth-child(even) {{background:rgba(10,26,58,0.5);}}
    </style>
    {html}
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────
# CORTEX AGENT CHAT
# ──────────────────────────────────────────────────────────────────
def call_agent(question: str, history: list) -> str:
    session = get_session()
    messages = []
    for m in history[-6:]:
        messages.append({"role": m["role"], "content": [{"type": "text", "text": m["content"]}]})
    messages.append({"role": "user", "content": [{"type": "text", "text": question}]})

    try:
        import _snowflake
        resp_raw = _snowflake.send_snow_api_request(
            "POST",
            "/api/v2/databases/DEMO_DEV/schemas/RETAIL_CATEGORY_ANALYTICS_AGENT/agents/RETAIL_CATEGORY_ANALYTICS_AGENT:run",
            {}, {},
            json.dumps({"messages": messages, "stream": False}),
            {}, 180000
        )
        if resp_raw:
            content = resp_raw if isinstance(resp_raw, str) else resp_raw.get("content", resp_raw.get("body", ""))
            resp = json.loads(content) if isinstance(content, str) else content

            # Extract tool usage from response
            tools_used = []
            choices = resp.get("choices", [])
            if choices:
                msg_content = choices[0].get("message", {}).get("content", [])
                if isinstance(msg_content, list):
                    for part in msg_content:
                        if isinstance(part, dict):
                            if part.get("type") == "tool_use":
                                tools_used.append(part.get("name", "unknown"))
                            elif part.get("type") == "tool_results":
                                tools_used.append(part.get("tool_name", "tool"))
                    text_parts = [p.get("text", "") for p in msg_content if isinstance(p, dict) and p.get("type") == "text"]
                    answer = " ".join(text_parts).strip()
                elif isinstance(msg_content, str):
                    answer = msg_content.strip()
                else:
                    answer = ""
                if answer:
                    st.session_state["last_tools_used"] = tools_used if tools_used else _infer_tools(question)
                    _log_conversation(session, question, answer, "")
                    return answer

            msg = resp.get("message", {})
            if isinstance(msg, dict) and msg.get("content"):
                content_val = msg["content"]
                if isinstance(content_val, list):
                    text_parts = [p.get("text", "") for p in content_val if isinstance(p, dict) and p.get("type") == "text"]
                    answer = " ".join(text_parts).strip()
                else:
                    answer = str(content_val).strip()
                if answer:
                    st.session_state["last_tools_used"] = _infer_tools(question)
                    _log_conversation(session, question, answer, "")
                    return answer

        return _fallback_analyst(session, question)
    except Exception:
        return _fallback_analyst(session, question)


def _infer_tools(question: str) -> list:
    """Infer which tools the agent likely used based on question keywords."""
    q = question.lower()
    tools = ["think"]
    if any(w in q for w in ["alert", "urgent", "critical", "review"]):
        tools.append("get_pricing_alerts")
    elif any(w in q for w in ["category", "health", "summary"]):
        tools.append("get_category_health")
    else:
        tools.append("query_pricing_data")
    tools.extend(["analyze", "respond"])
    return tools


def _fallback_analyst(session, question: str, error_info: str = "") -> str:
    try:
        q_lower = question.lower()
        # Set tools used for strategy loop
        st.session_state["last_tools_used"] = ["think", "query_pricing_data", "analyze", "respond"]
        if any(w in q_lower for w in ["promotion", "campaign", "roas", "lift", "under-perform", "over-perform", "promo"]):
            df = run_sql(f"""
                SELECT PROMOTION_NAME, TARGET_CATEGORY, PERFORMANCE_STATUS,
                       ROUND(ACTUAL_UNIT_LIFT_PCT, 1) AS ACTUAL_LIFT, ROUND(PLANNED_UNIT_LIFT_PCT, 1) AS PLANNED_LIFT,
                       ROUND(ESTIMATED_ROAS, 2) AS ROAS, ROUND(BUDGET_USD, 0) AS BUDGET
                FROM {SCHEMA}.GOLD_PROMOTION_PERFORMANCE
                ORDER BY ESTIMATED_ROAS DESC
            """)
        elif any(w in q_lower for w in ["churn", "loyalty", "customer", "ltv", "lifetime", "segment", "tier", "vip"]):
            df = run_sql(f"""
                SELECT FULL_NAME, TIER, CUSTOMER_SEGMENT, CHURN_RISK_LEVEL,
                       ROUND(ESTIMATED_LTV_USD, 0) AS LTV, ROUND(TOTAL_SPEND_USD, 0) AS SPEND,
                       DAYS_SINCE_LAST_PURCHASE
                FROM {SCHEMA}.GOLD_LOYALTY_CUSTOMER_INSIGHTS
                ORDER BY ESTIMATED_LTV_USD DESC LIMIT 10
            """)
        elif any(w in q_lower for w in ["return", "refund", "margin lost", "rationali", "defective"]):
            df = run_sql(f"""
                SELECT PRODUCT_NAME, BRAND, CATEGORY, TOTAL_RETURNS, RETURN_RATE_PCT,
                       ROUND(TOTAL_MARGIN_LOST_USD, 0) AS MARGIN_LOST, TOP_RETURN_REASON
                FROM {SCHEMA}.GOLD_RETURNS_MARGIN_ANALYSIS
                ORDER BY TOTAL_MARGIN_LOST_USD DESC LIMIT 10
            """)
        elif any(w in q_lower for w in ["alert", "urgent", "immediate", "review", "critical"]):
            df = run_sql(f"""
                SELECT SKU_ID, PRODUCT_NAME, CATEGORY, ROUND(OUR_CURRENT_PRICE,2) AS OUR_PRICE,
                       PRIMARY_COMPETITOR_NAME, ROUND(PRIMARY_COMPETITOR_PRICE,2) AS COMP_PRICE,
                       ROUND(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT,1) AS GAP_PCT
                FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
                WHERE REQUIRES_IMMEDIATE_PRICE_REVIEW = TRUE LIMIT 10
            """)
        elif any(w in q_lower for w in ["category", "health", "summary", "overview"]):
            df = run_sql(f"""
                SELECT CATEGORY, TOTAL_ACTIVE_SKUS_IN_CATEGORY, COUNT_OVERPRICED_SKUS,
                       ROUND(AVERAGE_MARGIN_PERCENTAGE,1) AS AVG_MARGIN
                FROM {SCHEMA}.GOLD_CATEGORY_PERFORMANCE_SUMMARY
            """)
        elif any(w in q_lower for w in ["stock", "inventory", "replenish"]):
            df = run_sql(f"""
                SELECT SKU_ID, PRODUCT_NAME, CURRENT_STOCK_LEVEL, STOCK_AVAILABILITY_STATUS
                FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
                WHERE REQUIRES_REPLENISHMENT_ACTION = TRUE LIMIT 10
            """)
        else:
            df = run_sql(f"""
                SELECT SKU_ID, PRODUCT_NAME, BRAND, ROUND(OUR_CURRENT_PRICE,2) AS OUR_PRICE,
                       ROUND(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT,1) AS GAP_PCT
                FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
                WHERE OVERALL_COMPETITIVE_POSITIONING_STATUS = 'OVERPRICED' LIMIT 10
            """)

        if not has_error(df):
            data_str = df.to_string(index=False, max_rows=10)
            q_escaped = question.replace("'", "''")
            data_escaped = data_str.replace("'", "''")[:3000]
            result = session.sql(f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2',
                    'You are a retail category analytics assistant. Answer concisely based on the data provided. Question: {q_escaped}\nData:\n{data_escaped}\nProvide 2-3 sentences with specific numbers from the data.') AS resp
            """).collect()
            if result and result[0][0]:
                answer = result[0][0]
                _log_conversation(session, question, answer, "")
                return answer
    except Exception:
        pass
    return "Unable to process. Try asking about: pricing, promotions, customer loyalty, or returns."


def _log_conversation(session, question: str, answer: str, sql_used: str):
    try:
        session_id = str(id(st.session_state))[:20]
        q_safe = question.replace("'", "''")[:2000]
        a_safe = answer.replace("'", "''")[:4000]
        s_safe = (sql_used or "").replace("'", "''")[:2000]
        session.sql(f"""
            INSERT INTO {SCHEMA}.GOLD_AGENT_CONVERSATION_LOG (
                CHAT_SESSION_IDENTIFIER, USER_QUESTION, AGENT_RESPONSE,
                SQL_QUERY_GENERATED, SNOWFLAKE_USERNAME
            ) VALUES ('{session_id}', '{q_safe}', '{a_safe}', '{s_safe}', CURRENT_USER())
        """).collect()
    except Exception:
        pass




# ──────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None
if "active_flow" not in st.session_state:
    st.session_state.active_flow = "Category Overview"
if "response_count" not in st.session_state:
    st.session_state.response_count = 0
if "last_tools_used" not in st.session_state:
    st.session_state.last_tools_used = []


# ══════════════════════════════════════════════════════════════════
# HEADER + ALERT TICKER + NAV TABS
# ══════════════════════════════════════════════════════════════════

# Logo, title, and powered-by — stacked top left
import base64, pathlib
_logo_path = pathlib.Path(__file__).parent / "Mastech Digital-White 4.svg"
_logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode()
st.markdown(
    '<div style="text-align:left;margin-bottom:4px">'
    '<img src="data:image/svg+xml;base64,{}" style="height:40px">'
    '</div>'.format(_logo_b64),
    unsafe_allow_html=True,
)
st.markdown('<h2 style="margin:0 0 2px 0;padding:0;color:#ecf6fd;font-weight:800;font-size:1.3rem;">Category Intelligence Platform</h2>', unsafe_allow_html=True)
st.markdown('<p style="margin:0 0 8px 0;padding:0;font-size:0.72rem;color:#8ec9f5;font-style:italic;">AI-Native Decision Platform Powered by Snowflake Cortex</p>', unsafe_allow_html=True)

# Alert ticker with "ALERTS" label
ticker_df = run_sql(f"""
    SELECT PRODUCT_NAME, ROUND(ABS(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT), 1) AS GAP_PCT
    FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
    WHERE REQUIRES_IMMEDIATE_PRICE_REVIEW = TRUE
      AND ABS(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT) > 10
    ORDER BY ABS(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT) DESC
    LIMIT 8
""")
if not has_error(ticker_df) and not ticker_df.empty:
    ticker_items = ""
    for _, row in ticker_df.iterrows():
        ticker_items += f'<span style="display:inline-block;padding:0 50px;">● {row["PRODUCT_NAME"]} — Price {row["GAP_PCT"]}% below market</span>'
    st.markdown(f"""
    <div style="display:flex;align-items:stretch;margin-bottom:8px;border-radius:4px;overflow:hidden;">
      <div style="background:#0d558b;padding:6px 14px;display:flex;align-items:center;white-space:nowrap;">
        <span style="color:#ffffff;font-weight:800;font-size:0.72rem;letter-spacing:0.05em;">⚡ ALERTS</span>
      </div>
      <div style="flex:1;overflow:hidden;background:linear-gradient(90deg,#01b8fb,#0d558b);padding:5px 0;">
        <div style="display:inline-block;white-space:nowrap;animation:ticker 35s linear infinite;color:#ffffff;font-size:0.76rem;">
          {ticker_items}{ticker_items}
        </div>
      </div>
    </div>
    <style>@keyframes ticker {{ 0% {{ transform:translateX(0); }} 100% {{ transform:translateX(-50%); }} }}</style>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# AGENT CHAT + CONTROL CENTER (always visible, above all tabs)
# ══════════════════════════════════════════════════════════════════
st.markdown('<hr style="margin:4px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)
agent_col, control_col = st.columns([8, 2])

with agent_col:
    st.markdown("""<div style="margin-bottom:6px;">
      <span style="font-size:0.9rem;font-weight:700;color:#ecf6fd;">Ask the 🤖 Category Intelligence Agent</span>
      <span style="font-size:0.75rem;color:#8ec9f5;margin-left:8px;font-style:italic;">— Get instant insights on pricing, margins, inventory & competitive gaps.</span>
    </div>""", unsafe_allow_html=True)

    # Suggested questions
    sq_cols = st.columns(5)
    suggested_click = None
    with sq_cols[0]:
        if st.button("Which SKUs need repricing?", key="suggestion_0", use_container_width=True):
            suggested_click = "Which SKUs need repricing?"
    with sq_cols[1]:
        if st.button("What's our stockout risk?", key="suggestion_1", use_container_width=True):
            suggested_click = "What's our stockout risk?"
    with sq_cols[2]:
        if st.button("Best performing categories?", key="suggestion_2", use_container_width=True):
            suggested_click = "Best performing categories?"
    with sq_cols[3]:
        if st.button("Top competitor threats?", key="suggestion_3", use_container_width=True):
            suggested_click = "Top competitor threats?"
    with sq_cols[4]:
        if st.button("Margin opportunities?", key="suggestion_4", use_container_width=True):
            suggested_click = "Margin improvement opportunities?"

    # Chat input
    input_cols = st.columns([9, 1])
    with input_cols[0]:
        user_input = st.text_input("Agent Chat", placeholder="Ask anything about category...", label_visibility="collapsed", key="agent_input")
    with input_cols[1]:
        ask_btn = st.button("→", key="agent_send_btn", use_container_width=True)
    # Style the send button with Mastech brand
    st.markdown("""<style>
    div[data-testid="stHorizontalBlock"]:has(button[key="agent_send_btn"]) [data-testid="stColumn"]:last-child button {
        background: linear-gradient(135deg, #01b8fb, #0d558b) !important;
        color: #ffffff !important;
        border: none !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 12px rgba(1,184,251,0.3) !important;
    }
    </style>""", unsafe_allow_html=True)

    # Submit logic
    submitted_question = None
    if suggested_click:
        submitted_question = suggested_click
    elif ask_btn and user_input.strip():
        submitted_question = user_input.strip()

    if submitted_question:
        with st.spinner("Agent reasoning..."):
            answer = call_agent(submitted_question, st.session_state.chat_history)
        st.session_state.chat_history.append({"role": "user", "content": submitted_question})
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.session_state.last_answer = answer
        st.session_state.response_count += 1
        st.rerun()

    # Chat history (scrollable)
    if st.session_state.chat_history:
        chat_html = ""
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""<div style="text-align:right;margin:4px 0;">
                  <span style="background:#01b8fb;color:#fff;border-radius:10px 10px 0 10px;padding:5px 10px;font-size:0.76rem;display:inline-block;max-width:80%;">{msg['content']}</span>
                </div>"""
            else:
                chat_html += f"""<div style="text-align:left;margin:4px 0;">
                  <span style="background:#0a1a3a;border:1px solid #1a3a5c;color:#ecf6fd;border-radius:10px 10px 10px 0;padding:5px 10px;font-size:0.76rem;display:inline-block;max-width:80%;line-height:1.4;">🤖 {msg['content']}</span>
                </div>"""
        st.markdown(f"""
        <style>
        .chat-scroll-container {{ max-height:180px !important; overflow-y:auto !important; padding:4px 8px; border:1px solid #1a3a5c; border-radius:8px; margin-top:6px; display:block !important; }}
        .chat-scroll-container::-webkit-scrollbar {{ width:4px; }}
        .chat-scroll-container::-webkit-scrollbar-thumb {{ background:#475569; border-radius:2px; }}
        [data-testid="stMarkdownContainer"]:has(.chat-scroll-container) {{ max-height:200px !important; overflow:hidden !important; }}
        </style>
        <div class="chat-scroll-container">
          {chat_html}
        </div>""", unsafe_allow_html=True)

with control_col:
    st.markdown('<p style="font-size:0.72rem;font-weight:700;color:#ecf6fd;margin:0 0 8px 0;padding-left:12px;border-left:1px solid #1a3a5c;">● AGENT STRATEGY LOOP</p>', unsafe_allow_html=True)

    rc = st.session_state.response_count
    tools_used = st.session_state.get("last_tools_used", [])

    # Tool name to display mapping
    tool_display = {
        "think": ("Think", "Reasoning over query"),
        "query_pricing_data": ("Query Data", "Cortex Analyst SQL generation"),
        "get_pricing_alerts": ("Get Alerts", "Fetching urgent price alerts"),
        "get_category_health": ("Category Health", "Loading category KPIs"),
        "execute_sku_action": ("Execute Action", "Running SKU action"),
        "analyze": ("Analyze", "Synthesizing results"),
        "respond": ("Respond", "Generating answer"),
    }

    if rc > 0 and tools_used:
        # Show actual tool chain with animated green checkmarks
        steps_html = ""
        for i, tool in enumerate(tools_used):
            display_name, desc = tool_display.get(tool, (tool.replace("_", " ").title(), "Processing"))
            delay = (i + 1) * 0.4
            steps_html += f"""<div class="step-r{rc}"><span class="icon">✓</span><span class="lbl">{display_name}</span><span class="dsc">— {desc}</span></div>"""

        st.markdown(f"""
        <style>
        @keyframes grayToGreen{rc} {{
          0% {{ color: #475569; }}
          100% {{ color: #4ade80; }}
        }}
        .step-r{rc} {{
          display:flex;align-items:center;gap:6px;padding:4px 0;padding-left:12px;border-left:1px solid #1a3a5c;
        }}
        .step-r{rc} .icon {{
          font-size:0.76rem;font-weight:700;color:#475569;
          animation: grayToGreen{rc} 0.3s forwards;
        }}
        .step-r{rc} .lbl {{
          font-size:0.74rem;font-weight:600;color:#475569;
          animation: grayToGreen{rc} 0.3s forwards;
        }}
        .step-r{rc} .dsc {{ font-size:0.66rem;color:#8ec9f5;font-style:italic; }}
        {"".join(f".step-r{rc}:nth-child({i+1}) .icon, .step-r{rc}:nth-child({i+1}) .lbl {{ animation-delay: {(i+1)*0.4}s; }}" for i in range(len(tools_used)))}
        </style>
        <div>{steps_html}</div>
        """, unsafe_allow_html=True)
    elif rc > 0:
        # Fallback: generic 4-step animation
        st.markdown(f"""
        <style>
        @keyframes grayToGreen{rc} {{ 0% {{ color: #475569; }} 100% {{ color: #4ade80; }} }}
        .step-r{rc} {{ display:flex;align-items:center;gap:6px;padding:4px 0;padding-left:12px;border-left:1px solid #1a3a5c; }}
        .step-r{rc} .icon {{ font-size:0.76rem;font-weight:700;color:#475569;animation: grayToGreen{rc} 0.3s forwards; }}
        .step-r{rc} .lbl {{ font-size:0.74rem;font-weight:600;color:#475569;animation: grayToGreen{rc} 0.3s forwards; }}
        .step-r{rc} .dsc {{ font-size:0.66rem;color:#8ec9f5;font-style:italic; }}
        .step-r{rc}:nth-child(1) .icon, .step-r{rc}:nth-child(1) .lbl {{ animation-delay: 0.5s; }}
        .step-r{rc}:nth-child(2) .icon, .step-r{rc}:nth-child(2) .lbl {{ animation-delay: 1.0s; }}
        .step-r{rc}:nth-child(3) .icon, .step-r{rc}:nth-child(3) .lbl {{ animation-delay: 1.5s; }}
        .step-r{rc}:nth-child(4) .icon, .step-r{rc}:nth-child(4) .lbl {{ animation-delay: 2.0s; }}
        </style>
        <div>
          <div class="step-r{rc}"><span class="icon">✓</span><span class="lbl">Think</span><span class="dsc">— Reasoning</span></div>
          <div class="step-r{rc}"><span class="icon">✓</span><span class="lbl">Query Data</span><span class="dsc">— SQL generation</span></div>
          <div class="step-r{rc}"><span class="icon">✓</span><span class="lbl">Analyze</span><span class="dsc">— Synthesizing</span></div>
          <div class="step-r{rc}"><span class="icon">✓</span><span class="lbl">Respond</span><span class="dsc">— Answering</span></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Idle state — all gray
        st.markdown("""
        <div>
          <div style="display:flex;align-items:center;gap:6px;padding:4px 0;padding-left:12px;border-left:1px solid #1a3a5c;"><span style="color:#475569;font-size:0.76rem;">○</span><span style="font-size:0.74rem;color:#ecf6fd;font-weight:600;">Think</span><span style="font-size:0.66rem;color:#8ec9f5;font-style:italic;">— Reasoning</span></div>
          <div style="display:flex;align-items:center;gap:6px;padding:4px 0;padding-left:12px;border-left:1px solid #1a3a5c;"><span style="color:#475569;font-size:0.76rem;">○</span><span style="font-size:0.74rem;color:#ecf6fd;font-weight:600;">Act</span><span style="font-size:0.66rem;color:#8ec9f5;font-style:italic;">— Fetching data</span></div>
          <div style="display:flex;align-items:center;gap:6px;padding:4px 0;padding-left:12px;border-left:1px solid #1a3a5c;"><span style="color:#475569;font-size:0.76rem;">○</span><span style="font-size:0.74rem;color:#ecf6fd;font-weight:600;">Analyze</span><span style="font-size:0.66rem;color:#8ec9f5;font-style:italic;">— Synthesizing</span></div>
          <div style="display:flex;align-items:center;gap:6px;padding:4px 0;padding-left:12px;border-left:1px solid #1a3a5c;"><span style="color:#475569;font-size:0.76rem;">○</span><span style="font-size:0.74rem;color:#ecf6fd;font-weight:600;">Respond</span><span style="font-size:0.66rem;color:#8ec9f5;font-style:italic;">— Answering</span></div>
        </div>
        """, unsafe_allow_html=True)

st.markdown('<hr style="margin:4px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

# Navigation tabs — using st.tabs() for native blue styling
tab_main_cat, tab_main_health, tab_main_sku, tab_main_price = st.tabs([
    "📊 Category Overview", "🩺 Health Check", "🔍 SKU Deep Dive", "💲 Price Simulation"
])



# ──────────────────────────────────────────────────────────────────
# SHARED KPI RENDERER
# ──────────────────────────────────────────────────────────────────
def render_kpi(label, value, delta, delta_direction="up"):
    cls = "kpi-delta-up" if delta_direction == "up" else "kpi-delta-down"
    arrow = "▲" if delta_direction == "up" else "▼"
    st.markdown(f"""
    <div class="kpi-card">
      <p class="kpi-label">{label}</p>
      <p class="kpi-value">{value}</p>
      <p class="kpi-delta {cls}">{arrow} {delta}</p>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# MAIN CONTENT — driven by st.tabs()
# ══════════════════════════════════════════════════════════════════

with tab_main_cat:
    # ─── TABS WITHIN CATEGORY OVERVIEW ───
    tab_cat, tab_promo, tab_loyalty, tab_returns = st.tabs([
        "⚡ Category",
        "🎯 Promotions & Campaigns",
        "💎 Customer Loyalty",
        "🔄 Returns & Margin Impact"
    ])

    with tab_cat:
        # Get real KPI data
        kpi_df = run_sql(f"""
            SELECT
                COUNT(*) AS TOTAL_SKUS,
                ROUND(AVG(OUR_MARGIN_PERCENTAGE), 1) AS AVG_MARGIN,
                ROUND(SUM(OUR_CURRENT_PRICE * CURRENT_STOCK_LEVEL), 0) AS INVENTORY_VALUE,
                COUNT(CASE WHEN OVERALL_COMPETITIVE_POSITIONING_STATUS='OVERPRICED' THEN 1 END) AS OVERPRICED,
                COUNT(CASE WHEN REQUIRES_IMMEDIATE_PRICE_REVIEW=TRUE THEN 1 END) AS NEEDS_ACTION,
                COUNT(CASE WHEN STOCK_AVAILABILITY_STATUS='OUT_OF_STOCK' THEN 1 END) AS OUT_OF_STOCK,
                COUNT(CASE WHEN STOCK_AVAILABILITY_STATUS='LOW_STOCK' THEN 1 END) AS LOW_STOCK,
                COUNT(CASE WHEN REQUIRES_REPLENISHMENT_ACTION=TRUE THEN 1 END) AS NEEDS_REPLENISH,
                ROUND(AVG(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT), 1) AS AVG_GAP
            FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
        """)

        # ─── KPI CARDS ───
        kpi_cols = st.columns(4)
        if not has_error(kpi_df):
            k = kpi_df.iloc[0]
            total_skus = int(k.TOTAL_SKUS)
            inv_value = int(k.INVENTORY_VALUE) if k.INVENTORY_VALUE else 0
            overpriced = int(k.OVERPRICED)
            needs_action = int(k.NEEDS_ACTION)
            out_of_stock = int(k.OUT_OF_STOCK)
            low_stock = int(k.LOW_STOCK)
            needs_replenish = int(k.NEEDS_REPLENISH)
            avg_margin = float(k.AVG_MARGIN) if k.AVG_MARGIN else 0
            avg_gap = float(k.AVG_GAP) if k.AVG_GAP else 0

            with kpi_cols[0]:
                inv_display = f"${inv_value:,}" if inv_value < 1000000 else f"${inv_value/1000000:.1f}M"
                render_kpi("INVENTORY VALUE", inv_display, f"{total_skus} active SKUs", "up")
            with kpi_cols[1]:
                render_kpi("AVG MARGIN %", f"{avg_margin}%", f"Avg gap {avg_gap}% vs competitors", "up" if avg_margin > 15 else "down")
            with kpi_cols[2]:
                stockout_risk = out_of_stock + low_stock
                render_kpi("STOCKOUT RISK", f"{stockout_risk} SKUs", f"{out_of_stock} Out of Stock + {low_stock} Low Stock", "down" if stockout_risk > 5 else "up")
            with kpi_cols[3]:
                render_kpi("URGENT REPRICE", f"{needs_action} SKUs", f"{overpriced} priced above market", "down" if needs_action > 3 else "up")
        else:
            for col in kpi_cols:
                with col:
                    render_kpi("—", "—", "No data", "up")

        # ═══════════════════════════════════════════════════════════
        # 2-PANEL LAYOUT: Weekly Brand Performance | SKU Performance Detail
        # ═══════════════════════════════════════════════════════════
        st.markdown('<hr style="margin:6px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)
        col_chart, col_sku = st.columns([6, 4])

        # ─── PANEL 1: WEEKLY BRAND PERFORMANCE ───
        with col_chart:
            st.markdown("**📈 13-Week Sell-Through Trend — Units by Brand** _(Oct–Dec 2024)_")

            # Load data
            trend_raw_df = run_sql(f"""
                SELECT WEEK_START_DATE, BRAND, TOTAL_UNITS_SOLD
                FROM {SCHEMA}.GOLD_WEEKLY_BRAND_SELL_THROUGH
                ORDER BY WEEK_START_DATE, BRAND
            """)

            if not has_error(trend_raw_df) and not trend_raw_df.empty:
                # Convert dates
                trend_raw_df["WEEK_START_DATE"] = pd.to_datetime(trend_raw_df["WEEK_START_DATE"])

                # Filters (compact row)
                filter_cols = st.columns([3, 3, 3])
                with filter_cols[0]:
                    all_brands = sorted(trend_raw_df["BRAND"].unique().tolist())
                    selected_brand = st.selectbox("Brand", options=["All Brands"] + all_brands, key="trend_brand_filter")
                with filter_cols[1]:
                    min_date = trend_raw_df["WEEK_START_DATE"].min().date()
                    max_date = trend_raw_df["WEEK_START_DATE"].max().date()
                    start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="trend_start_date")
                with filter_cols[2]:
                    end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="trend_end_date")

                # Apply filters
                trend_df = trend_raw_df[
                    (trend_raw_df["WEEK_START_DATE"].dt.date >= start_date) &
                    (trend_raw_df["WEEK_START_DATE"].dt.date <= end_date)
                ].copy()
                if selected_brand != "All Brands":
                    trend_df = trend_df[trend_df["BRAND"] == selected_brand]

                # Format x-axis
                trend_df["WEEK"] = trend_df["WEEK_START_DATE"].dt.strftime("%b %d")

                if not trend_df.empty:
                    pivot_df = trend_df.pivot_table(index="WEEK_START_DATE", columns="BRAND", values="TOTAL_UNITS_SOLD", fill_value=0)
                    pivot_df = pivot_df.sort_index()
                    # Create ordered labels
                    date_labels = [d.strftime('%b %d') for d in pivot_df.index]
                    pivot_df.index = pd.CategoricalIndex(date_labels, categories=date_labels, ordered=True)
                    st.line_chart(pivot_df, height=300)
                else:
                    st.info("No data for selected filters.")
            else:
                st.info("No sell-through data available.")

        # ─── PANEL 2: SKU PERFORMANCE + ALERTS ───
        with col_sku:
            st.markdown("**📋 SKU Performance Detail**")
            all_sku_df = run_sql(f"""
                SELECT
                    PRODUCT_NAME AS "Product",
                    ROUND(OUR_MARGIN_PERCENTAGE, 1) AS "Margin %",
                    OVERALL_COMPETITIVE_POSITIONING_STATUS AS "Status",
                    STOCK_AVAILABILITY_STATUS AS "Stock"
                FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
                ORDER BY ABS(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT) DESC
            """)
            if not has_error(all_sku_df) and not all_sku_df.empty:
                render_table(all_sku_df.reset_index(drop=True), max_height="220px")
            else:
                st.info("No SKU data available.")

            show_alerts = st.checkbox("🚨 Pricing Alerts — Click to view critical issues", key="show_pricing_alerts")
            if show_alerts:
                alert_df = run_sql(f"""
                    SELECT PRODUCT_NAME, BRAND, CATEGORY,
                           ROUND(OUR_CURRENT_PRICE, 2) AS OUR_PRICE,
                           PRIMARY_COMPETITOR_NAME,
                           ROUND(PRIMARY_COMPETITOR_PRICE, 2) AS COMP_PRICE,
                           ROUND(ABS(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT), 1) AS GAP_PCT,
                           STOCK_AVAILABILITY_STATUS,
                           CURRENT_STOCK_LEVEL,
                           CORTEX_AI_RECOMMENDATION_SUMMARY
                    FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
                    WHERE REQUIRES_IMMEDIATE_PRICE_REVIEW = TRUE
                      AND ABS(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT) > 10
                    ORDER BY ABS(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT) DESC
                    LIMIT 5
                """)
                if not has_error(alert_df) and not alert_df.empty:
                    for _, row in alert_df.iterrows():
                        rec = row["CORTEX_AI_RECOMMENDATION_SUMMARY"] or "Review pricing strategy for this SKU."
                        stock_color = "#fbbf24" if row["STOCK_AVAILABILITY_STATUS"] == "OUT_OF_STOCK" else ("#fbbf24" if row["STOCK_AVAILABILITY_STATUS"] == "LOW_STOCK" else "#4ade80")
                        st.markdown(f"""
                        <div style="background:#0a1a3a;border-left:3px solid #fbbf24;border-radius:0 8px 8px 0;padding:10px 12px;margin:8px 0;">
                          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                            <span style="font-size:0.82rem;font-weight:700;color:#ecf6fd;">{row['PRODUCT_NAME']}</span>
                            <span style="font-size:0.68rem;color:{stock_color};font-weight:600;">{row['STOCK_AVAILABILITY_STATUS'].replace('_', ' ')}</span>
                          </div>
                          <p style="font-size:0.72rem;color:#8ec9f5;margin:2px 0;">{row['BRAND']} · {row['CATEGORY']} · Stock: {row['CURRENT_STOCK_LEVEL']} units</p>
                          <p style="font-size:0.72rem;color:#8ec9f5;margin:2px 0;">Our Price: <b style="color:#ecf6fd;">${row['OUR_PRICE']}</b> vs {row['PRIMARY_COMPETITOR_NAME']}: <b style="color:#ecf6fd;">${row['COMP_PRICE']}</b> · Gap: <span style="color:#fbbf24;font-weight:700;">{row['GAP_PCT']}%</span></p>
                          <p style="font-size:0.72rem;color:#01b8fb;margin:4px 0 0 0;font-style:italic;">🤖 AI: {rec[:150]}{'...' if len(str(rec)) > 150 else ''}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown('<p style="font-size:0.78rem;color:#4ade80;">No active alerts.</p>', unsafe_allow_html=True)

    with tab_promo:

        # ─── LOAD DATA UPFRONT FOR AI INSIGHT ───
        promo_kpi_df = run_sql(f"""
            SELECT
                COUNT(*) AS TOTAL_CAMPAIGNS,
                COUNT(CASE WHEN PERFORMANCE_STATUS = 'OVER_PERFORMING' THEN 1 END) AS OVER_PERFORMING,
                COUNT(CASE WHEN PERFORMANCE_STATUS = 'ON_TRACK' THEN 1 END) AS ON_TRACK,
                COUNT(CASE WHEN PERFORMANCE_STATUS = 'UNDER_PERFORMING' THEN 1 END) AS UNDER_PERFORMING,
                ROUND(SUM(TOTAL_REVENUE_DURING_PROMO), 0) AS TOTAL_PROMO_REVENUE,
                ROUND(AVG(ACTUAL_UNIT_LIFT_PCT), 1) AS AVG_LIFT,
                ROUND(AVG(ESTIMATED_ROAS), 1) AS AVG_ROAS,
                ROUND(SUM(BUDGET_USD), 0) AS TOTAL_SPEND
            FROM {SCHEMA}.GOLD_PROMOTION_PERFORMANCE
        """)

        promo_detail_df = run_sql(f"""
            SELECT PROMOTION_NAME, PROMOTION_TYPE, TARGET_CATEGORY, TARGET_BRAND, CHANNEL,
                   START_DATE, END_DATE, PERFORMANCE_STATUS,
                   ACTUAL_UNIT_LIFT_PCT, PLANNED_UNIT_LIFT_PCT,
                   ROUND(TOTAL_REVENUE_DURING_PROMO, 0) AS REVENUE,
                   ESTIMATED_ROAS, SKU_COUNT, TOTAL_UNITS_DURING_PROMO
            FROM {SCHEMA}.GOLD_PROMOTION_PERFORMANCE
            ORDER BY START_DATE DESC
        """)

        # ─── AI INSIGHT (TOP BANNER) ───
        if not has_error(promo_kpi_df) and not has_error(promo_detail_df) and not promo_detail_df.empty:
            over_count = int(promo_kpi_df.iloc[0].OVER_PERFORMING)
            under_count = int(promo_kpi_df.iloc[0].UNDER_PERFORMING)
            on_track_count = int(promo_kpi_df.iloc[0].ON_TRACK)
            avg_roas = float(promo_kpi_df.iloc[0].AVG_ROAS)
            avg_lift = float(promo_kpi_df.iloc[0].AVG_LIFT)
            total_campaigns = int(promo_kpi_df.iloc[0].TOTAL_CAMPAIGNS)
            best_promo = promo_detail_df.loc[promo_detail_df["ESTIMATED_ROAS"].idxmax(), "PROMOTION_NAME"]
            best_roas = float(promo_detail_df["ESTIMATED_ROAS"].max())
            worst_promo = promo_detail_df.loc[promo_detail_df["ESTIMATED_ROAS"].idxmin(), "PROMOTION_NAME"]
            worst_roas = float(promo_detail_df["ESTIMATED_ROAS"].min())

            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #0f2027 0%, #1a2332 50%, #0d1b2a 100%);
                        border:1px solid #01b8fb; border-radius:10px; padding:14px 18px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; margin-bottom:6px;">
                    <span style="font-size:1rem; margin-right:8px;">🧠</span>
                    <span style="font-size:0.8rem; font-weight:700; color:#01b8fb; text-transform:uppercase; letter-spacing:0.05em;">
                        AI Campaign Intelligence
                    </span>
                </div>
                <p style="color:#ecf6fd; font-size:0.84rem; line-height:1.5; margin:0 0 8px 0;">
                    Analyzing <b>{total_campaigns}</b> active campaigns:
                    <span style="color:#4ade80;font-weight:600;">{over_count} exceeding targets</span>,
                    <span style="color:#fbbf24;font-weight:600;">{on_track_count} on track</span>,
                    <span style="color:#fbbf24;font-weight:600;">{under_count} need attention</span>.
                    Portfolio is delivering <b>{avg_lift}%</b> average lift at <b>{avg_roas}x</b> ROAS.
                </p>
                <div style="display:flex;gap:16px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:200px;background:#0d2818;border:1px solid #166534;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#4ade80;font-weight:700;margin:0;text-transform:uppercase;">✓ Top Performer</p>
                        <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{best_promo}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">{best_roas}x ROAS — Scale budget allocation here</p>
                    </div>
                    <div style="flex:1;min-width:200px;background:#1c1007;border:1px solid #92400e;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#fbbf24;font-weight:700;margin:0;text-transform:uppercase;">⚠ Needs Review</p>
                        <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{worst_promo}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">{worst_roas}x ROAS — Consider pausing or reallocating budget</p>
                    </div>
                    <div style="flex:1;min-width:200px;background:#030c25;border:1px solid #1e40af;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#60a5fa;font-weight:700;margin:0;text-transform:uppercase;">💡 Recommendation</p>
                        <p style="font-size:0.72rem;color:#ecf6fd;margin:2px 0;line-height:1.4;">Shift {under_count} under-performing campaign budgets to high-ROAS channels. Expected portfolio ROAS improvement: +{round(best_roas - avg_roas, 1)}x</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ─── KPI ROW ───
        if not has_error(promo_kpi_df):
            pk = promo_kpi_df.iloc[0]
            pk_cols = st.columns(4)
            with pk_cols[0]:
                render_kpi("TOTAL CAMPAIGNS", str(int(pk.TOTAL_CAMPAIGNS)), f"{int(pk.OVER_PERFORMING)} over-performing", "up")
            with pk_cols[1]:
                rev = int(pk.TOTAL_PROMO_REVENUE) if pk.TOTAL_PROMO_REVENUE else 0
                rev_display = f"${rev:,}" if rev < 1000000 else f"${rev/1000000:.1f}M"
                render_kpi("PROMO REVENUE", rev_display, f"${int(pk.TOTAL_SPEND):,} spend", "up")
            with pk_cols[2]:
                render_kpi("AVG UNIT LIFT", f"{float(pk.AVG_LIFT)}%", f"{int(pk.ON_TRACK)} on track, {int(pk.UNDER_PERFORMING)} under", "up" if float(pk.AVG_LIFT) > 20 else "down")
            with pk_cols[3]:
                render_kpi("AVG ROAS", f"{float(pk.AVG_ROAS)}x", "Revenue / Marketing Spend", "up" if float(pk.AVG_ROAS) > 2 else "down")

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── CAMPAIGN CARDS ───
        st.markdown("**Campaign Performance**")

        if not has_error(promo_detail_df) and not promo_detail_df.empty:
            # Campaign status cards — show top 4
            card_cols = st.columns(4)
            for idx, row in promo_detail_df.head(4).iterrows():
                with card_cols[idx % 4]:
                    status = row["PERFORMANCE_STATUS"]
                    color = "#4ade80" if status == "OVER_PERFORMING" else ("#fbbf24" if status == "ON_TRACK" else "#fbbf24")
                    status_label = status.replace("_", " ").title()
                    st.markdown(f"""
                    <div style="background:#0a1a3a;border:1px solid #1a3a5c;border-radius:8px;padding:12px;margin-bottom:8px;">
                        <p style="font-size:0.75rem;font-weight:700;color:#8ec9f5;margin:0;">{row['PROMOTION_TYPE']}</p>
                        <p style="font-size:0.95rem;font-weight:700;color:#ecf6fd;margin:4px 0;">{row['PROMOTION_NAME']}</p>
                        <p style="margin:2px 0;"><span style="color:{color};font-weight:700;font-size:0.8rem;">{status_label}</span></p>
                        <p style="font-size:0.75rem;color:#8ec9f5;margin:2px 0;">Lift: {row['ACTUAL_UNIT_LIFT_PCT']}% actual vs {row['PLANNED_UNIT_LIFT_PCT']}% planned</p>
                        <p style="font-size:0.75rem;color:#8ec9f5;margin:2px 0;">ROAS: {row['ESTIMATED_ROAS']}x · {row['SKU_COUNT']} SKUs · {row['TOTAL_UNITS_DURING_PROMO']} units</p>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")

            # ─── CAMPAIGN ACTION BOARD ───
            st.markdown("**Campaign Action Board** — _Prioritized by what needs attention first_")
            
            # Build actionable view
            action_df = promo_detail_df.copy()
            action_df["LIFT_GAP"] = action_df["ACTUAL_UNIT_LIFT_PCT"] - action_df["PLANNED_UNIT_LIFT_PCT"]
            action_df["LIFT_VS_PLAN"] = action_df.apply(
                lambda r: f"{r['ACTUAL_UNIT_LIFT_PCT']}% vs {r['PLANNED_UNIT_LIFT_PCT']}% ({'+' if r['LIFT_GAP'] >= 0 else ''}{round(r['LIFT_GAP'], 1)}pts)", axis=1)
            action_df["ACTION"] = action_df["PERFORMANCE_STATUS"].map({
                "UNDER_PERFORMING": "Reallocate budget or pause",
                "ON_TRACK": "Monitor & maintain",
                "OVER_PERFORMING": "Scale up investment"
            })
            action_df["STATUS_SORT"] = action_df["PERFORMANCE_STATUS"].map({
                "UNDER_PERFORMING": 0, "ON_TRACK": 1, "OVER_PERFORMING": 2
            })
            action_df = action_df.sort_values("STATUS_SORT")
            
            display_action = action_df[["PROMOTION_NAME", "PERFORMANCE_STATUS", "LIFT_VS_PLAN", "ESTIMATED_ROAS", "REVENUE", "ACTION"]].rename(columns={
                "PROMOTION_NAME": "Campaign",
                "PERFORMANCE_STATUS": "Status",
                "LIFT_VS_PLAN": "Actual vs Planned Lift",
                "ESTIMATED_ROAS": "ROAS",
                "REVENUE": "Revenue ($)",
                "ACTION": "Recommended Action"
            })
            render_table(display_action.reset_index(drop=True))
        else:
            st.info("No promotion performance data available. Ensure the promotions pipeline has been populated.")


    with tab_loyalty:
        # ─── LOAD DATA ───
        loyalty_kpi_df = run_sql(f"""
            SELECT
                COUNT(*) AS TOTAL_MEMBERS,
                COUNT(CASE WHEN STATUS = 'ACTIVE' THEN 1 END) AS ACTIVE_MEMBERS,
                COUNT(CASE WHEN CHURN_RISK_LEVEL = 'HIGH' THEN 1 END) AS HIGH_RISK,
                COUNT(CASE WHEN CUSTOMER_SEGMENT = 'VIP' THEN 1 END) AS VIP_COUNT,
                ROUND(AVG(ESTIMATED_LTV_USD), 0) AS AVG_LTV,
                ROUND(AVG(AVG_ORDER_VALUE), 0) AS AVG_AOV,
                ROUND(SUM(TOTAL_SPEND_USD), 0) AS TOTAL_LOYALTY_REVENUE,
                ROUND(SUM(POINTS_REDEEMABLE_VALUE_USD), 0) AS TOTAL_POINTS_VALUE,
                ROUND(SUM(CASE WHEN CHURN_RISK_LEVEL = 'HIGH' THEN ESTIMATED_LTV_USD ELSE 0 END), 0) AS REVENUE_AT_RISK
            FROM {SCHEMA}.GOLD_LOYALTY_CUSTOMER_INSIGHTS
        """)

        loyalty_detail_df = run_sql(f"""
            SELECT FULL_NAME, TIER, CUSTOMER_SEGMENT, STATUS, TOP_CATEGORY, TOP_BRAND,
                   TOTAL_TRANSACTIONS, ROUND(TOTAL_SPEND_USD, 0) AS TOTAL_SPEND,
                   ROUND(AVG_ORDER_VALUE, 0) AS AVG_ORDER, ROUND(ESTIMATED_LTV_USD, 0) AS LTV,
                   CHURN_RISK_LEVEL, DAYS_SINCE_LAST_PURCHASE, RECOMMENDED_ACTION
            FROM {SCHEMA}.GOLD_LOYALTY_CUSTOMER_INSIGHTS
            ORDER BY ESTIMATED_LTV_USD DESC
        """)

        segment_df = run_sql(f"""
            SELECT CUSTOMER_SEGMENT, COUNT(*) AS MEMBERS,
                   ROUND(SUM(ESTIMATED_LTV_USD), 0) AS TOTAL_LTV,
                   ROUND(AVG(ESTIMATED_LTV_USD), 0) AS AVG_LTV,
                   COUNT(CASE WHEN CHURN_RISK_LEVEL = 'HIGH' THEN 1 END) AS HIGH_RISK_COUNT,
                   ROUND(SUM(CASE WHEN CHURN_RISK_LEVEL = 'HIGH' THEN ESTIMATED_LTV_USD ELSE 0 END), 0) AS LTV_AT_RISK
            FROM {SCHEMA}.GOLD_LOYALTY_CUSTOMER_INSIGHTS
            GROUP BY CUSTOMER_SEGMENT
            ORDER BY TOTAL_LTV DESC
        """)

        # ─── AI INSIGHT BANNER (with action cards) ───
        if not has_error(loyalty_kpi_df) and not has_error(loyalty_detail_df) and not loyalty_detail_df.empty:
            lk = loyalty_kpi_df.iloc[0]
            high_risk = int(lk.HIGH_RISK)
            vip_count = int(lk.VIP_COUNT)
            total_members = int(lk.TOTAL_MEMBERS)
            avg_ltv = int(lk.AVG_LTV)
            total_rev = int(lk.TOTAL_LOYALTY_REVENUE)
            rev_at_risk = int(lk.REVENUE_AT_RISK)

            # Find highest-value at-risk customer
            high_risk_df = loyalty_detail_df[loyalty_detail_df["CHURN_RISK_LEVEL"] == "HIGH"]
            top_risk_name = high_risk_df.iloc[0]["FULL_NAME"] if not high_risk_df.empty else "N/A"
            top_risk_ltv = int(high_risk_df.iloc[0]["LTV"]) if not high_risk_df.empty else 0

            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #0f2027 0%, #1a2332 50%, #0d1b2a 100%);
                        border:1px solid #01b8fb; border-radius:10px; padding:14px 18px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; margin-bottom:6px;">
                    <span style="font-size:1rem; margin-right:8px;">🧠</span>
                    <span style="font-size:0.8rem; font-weight:700; color:#01b8fb; text-transform:uppercase; letter-spacing:0.05em;">
                        AI Customer Intelligence
                    </span>
                </div>
                <p style="color:#ecf6fd; font-size:0.84rem; line-height:1.5; margin:0 0 8px 0;">
                    <b>{total_members}</b> loyalty members generating <b>${total_rev:,}</b> in lifetime revenue.
                    <span style="color:#4ade80;font-weight:600;">{vip_count} VIPs</span> drive highest value.
                    <span style="color:#fbbf24;font-weight:600;">{high_risk} members</span> at high churn risk with
                    <span style="color:#fbbf24;font-weight:600;">${rev_at_risk:,}</span> revenue at stake.
                </p>
                <div style="display:flex;gap:16px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:200px;background:#1c1007;border:1px solid #92400e;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#fbbf24;font-weight:700;margin:0;text-transform:uppercase;">🚨 Revenue at Risk</p>
                        <p style="font-size:1.1rem;color:#ecf6fd;margin:2px 0;font-weight:700;">${rev_at_risk:,}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">{high_risk} high-churn members — Act now to retain</p>
                    </div>
                    <div style="flex:1;min-width:200px;background:#0d2818;border:1px solid #166534;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#4ade80;font-weight:700;margin:0;text-transform:uppercase;">✓ Top at-Risk Customer</p>
                        <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{top_risk_name}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">LTV: ${top_risk_ltv:,} — Priority re-engagement target</p>
                    </div>
                    <div style="flex:1;min-width:200px;background:#030c25;border:1px solid #1e40af;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#60a5fa;font-weight:700;margin:0;text-transform:uppercase;">💡 Retention Opportunity</p>
                        <p style="font-size:0.72rem;color:#ecf6fd;margin:2px 0;line-height:1.4;">Retain {high_risk} at-risk members to protect ${rev_at_risk:,} in LTV. Target with personalized offers based on top category preferences.</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ─── KPI ROW ───
        if not has_error(loyalty_kpi_df):
            lk = loyalty_kpi_df.iloc[0]
            lk_cols = st.columns(4)
            with lk_cols[0]:
                render_kpi("ACTIVE MEMBERS", str(int(lk.ACTIVE_MEMBERS)), f"{int(lk.TOTAL_MEMBERS)} total enrolled", "up")
            with lk_cols[1]:
                render_kpi("AVG LIFETIME VALUE", f"${int(lk.AVG_LTV):,}", f"${int(lk.TOTAL_LOYALTY_REVENUE):,} total revenue", "up")
            with lk_cols[2]:
                render_kpi("REVENUE AT RISK", f"${int(lk.REVENUE_AT_RISK):,}", f"{int(lk.HIGH_RISK)} high-churn members", "down")
            with lk_cols[3]:
                render_kpi("AVG ORDER VALUE", f"${int(lk.AVG_AOV):,}", f"{int(lk.VIP_COUNT)} VIP members", "up")

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── SEGMENT RISK BREAKDOWN ───
        st.markdown("**Customer Segment Overview** — _Revenue concentration & churn risk by segment_")
        if not has_error(segment_df) and not segment_df.empty:
            seg_cols = st.columns(len(segment_df))
            seg_colors = {"VIP": "#a78bfa", "LOYAL": "#4ade80", "AT_RISK": "#fbbf24", "NEW": "#60a5fa", "DORMANT": "#64748b"}
            for idx, row in segment_df.iterrows():
                with seg_cols[idx]:
                    color = seg_colors.get(row["CUSTOMER_SEGMENT"], "#8ec9f5")
                    risk_pct = round(row["HIGH_RISK_COUNT"] / row["MEMBERS"] * 100, 0) if row["MEMBERS"] > 0 else 0
                    st.markdown(f"""
                    <div style="background:#0a1a3a;border:1px solid #1a3a5c;border-radius:8px;padding:10px;text-align:center;">
                        <p style="font-size:0.72rem;font-weight:700;color:{color};margin:0;text-transform:uppercase;">{row['CUSTOMER_SEGMENT']}</p>
                        <p style="font-size:1.2rem;font-weight:700;color:#ecf6fd;margin:2px 0;">{row['MEMBERS']}</p>
                        <p style="font-size:0.68rem;color:#8ec9f5;margin:2px 0;">LTV: ${row['TOTAL_LTV']:,}</p>
                        <p style="font-size:0.68rem;color:#8ec9f5;margin:2px 0;">Avg: ${row['AVG_LTV']:,}</p>
                        <p style="font-size:0.68rem;color:#fbbf24;margin:2px 0;">{int(row['HIGH_RISK_COUNT'])} at risk ({int(risk_pct)}%)</p>
                        <p style="font-size:0.68rem;color:#fbbf24;margin:2px 0;">${row['LTV_AT_RISK']:,} at stake</p>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── CUSTOMER ACTION BOARD ───
        st.markdown("**Customer Action Board** — _Prioritized by revenue at risk (who to save first)_")
        st.markdown("""<div style="font-size:0.65rem;color:#64748b;margin-bottom:6px;line-height:1.6;">
            <b style="color:#8ec9f5;">Column Guide:</b>
            <b>LTV ($)</b> = Estimated lifetime value based on spend history |
            <b>Days Inactive</b> = Days since last purchase |
            <b>Risk</b> = Churn probability (HIGH/MEDIUM/LOW) based on inactivity & spend decline |
            <b>Action</b> = AI-recommended retention strategy
        </div>""", unsafe_allow_html=True)
        if not has_error(loyalty_detail_df) and not loyalty_detail_df.empty:
            # Filters
            filt_c1, filt_c2, filt_c3 = st.columns(3)
            with filt_c1:
                tier_filter = st.selectbox("Tier", ["All Tiers", "PLATINUM", "GOLD", "SILVER", "STANDARD"], key="loy_tier_filter")
            with filt_c2:
                seg_filter = st.selectbox("Segment", ["All Segments", "VIP", "LOYAL", "AT_RISK", "NEW", "DORMANT"], key="loy_seg_filter")
            with filt_c3:
                risk_filter = st.selectbox("Churn Risk", ["All Risk Levels", "HIGH", "MEDIUM", "LOW"], key="loy_risk_filter")

            filtered_df = loyalty_detail_df.copy()
            if tier_filter != "All Tiers":
                filtered_df = filtered_df[filtered_df["TIER"] == tier_filter]
            if seg_filter != "All Segments":
                filtered_df = filtered_df[filtered_df["CUSTOMER_SEGMENT"] == seg_filter]
            if risk_filter != "All Risk Levels":
                filtered_df = filtered_df[filtered_df["CHURN_RISK_LEVEL"] == risk_filter]

            # Sort by risk (HIGH first) then by LTV (highest first)
            risk_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            filtered_df["RISK_SORT"] = filtered_df["CHURN_RISK_LEVEL"].map(risk_order)
            filtered_df = filtered_df.sort_values(["RISK_SORT", "LTV"], ascending=[True, False])

            # Map actions to descriptive recommendations
            action_map = {
                "UPSELL": "Offer premium tier upgrade with exclusive benefits",
                "RETAIN": "Send personalized loyalty reward & exclusive discount",
                "RE_ENGAGE": "Trigger win-back campaign with time-limited offer",
                "ONBOARD": "Send welcome series with first-purchase incentive"
            }
            filtered_df["ACTION_DESC"] = filtered_df["RECOMMENDED_ACTION"].map(action_map).fillna(filtered_df["RECOMMENDED_ACTION"])

            display_loyalty_df = filtered_df[["FULL_NAME", "TIER", "CUSTOMER_SEGMENT", "LTV", "DAYS_SINCE_LAST_PURCHASE", "CHURN_RISK_LEVEL", "ACTION_DESC"]].rename(columns={
                "FULL_NAME": "Customer",
                "TIER": "Tier",
                "CUSTOMER_SEGMENT": "Segment",
                "LTV": "LTV ($)",
                "DAYS_SINCE_LAST_PURCHASE": "Days Inactive",
                "CHURN_RISK_LEVEL": "Risk",
                "ACTION_DESC": "Recommended Action"
            })

            st.caption(f"Showing {len(display_loyalty_df)} members — sorted by risk & lifetime value")
            render_table(display_loyalty_df.reset_index(drop=True))
        else:
            st.info("No loyalty data available.")


    with tab_returns:
        # ─── LOAD DATA ───
        returns_kpi_df = run_sql(f"""
            SELECT
                COUNT(*) AS TOTAL_RETURN_SKUS,
                SUM(TOTAL_RETURNS) AS TOTAL_RETURNS,
                ROUND(SUM(TOTAL_MARGIN_LOST_USD), 0) AS TOTAL_MARGIN_LOST,
                ROUND(AVG(RETURN_RATE_PCT), 2) AS AVG_RETURN_RATE,
                COUNT(CASE WHEN RATIONALIZATION_FLAG = TRUE THEN 1 END) AS SKUS_TO_RATIONALIZE,
                ROUND(SUM(TOTAL_REFUND_USD), 0) AS TOTAL_REFUNDS,
                ROUND(SUM(CASE WHEN RATIONALIZATION_FLAG = TRUE THEN TOTAL_MARGIN_LOST_USD ELSE 0 END), 0) AS RECOVERABLE_MARGIN
            FROM {SCHEMA}.GOLD_RETURNS_MARGIN_ANALYSIS
        """)

        returns_detail_df = run_sql(f"""
            SELECT PRODUCT_NAME, BRAND, CATEGORY, TOTAL_RETURNS, TOTAL_UNITS_SOLD,
                   RETURN_RATE_PCT, ROUND(TOTAL_MARGIN_LOST_USD, 0) AS MARGIN_LOST,
                   ROUND(TOTAL_REFUND_USD, 0) AS REFUND_TOTAL, ROUND(AVG_DAYS_TO_RETURN, 0) AS AVG_DAYS,
                   TOP_RETURN_REASON, RECOMMENDED_ACTION, RATIONALIZATION_FLAG
            FROM {SCHEMA}.GOLD_RETURNS_MARGIN_ANALYSIS
            ORDER BY TOTAL_MARGIN_LOST_USD DESC
        """)

        returns_by_category = run_sql(f"""
            SELECT CATEGORY, ROUND(SUM(TOTAL_MARGIN_LOST_USD), 0) AS MARGIN_LOST,
                   SUM(TOTAL_RETURNS) AS RETURNS
            FROM {SCHEMA}.GOLD_RETURNS_MARGIN_ANALYSIS
            GROUP BY CATEGORY ORDER BY MARGIN_LOST DESC
        """)

        returns_by_reason = run_sql(f"""
            SELECT TOP_RETURN_REASON, COUNT(*) AS SKU_COUNT,
                   ROUND(SUM(TOTAL_MARGIN_LOST_USD), 0) AS MARGIN_LOST,
                   SUM(TOTAL_RETURNS) AS RETURNS
            FROM {SCHEMA}.GOLD_RETURNS_MARGIN_ANALYSIS
            GROUP BY TOP_RETURN_REASON ORDER BY MARGIN_LOST DESC
        """)

        # ─── AI INSIGHT BANNER (with action cards) ───
        if not has_error(returns_kpi_df) and not has_error(returns_detail_df) and not returns_detail_df.empty:
            rk = returns_kpi_df.iloc[0]
            total_margin_lost = int(rk.TOTAL_MARGIN_LOST)
            total_returns = int(rk.TOTAL_RETURNS)
            avg_rate = float(rk.AVG_RETURN_RATE)
            skus_flagged = int(rk.SKUS_TO_RATIONALIZE)
            recoverable = int(rk.RECOVERABLE_MARGIN)
            worst_sku = returns_detail_df.iloc[0]["PRODUCT_NAME"]
            worst_margin = int(returns_detail_df.iloc[0]["MARGIN_LOST"])
            top_reason = returns_detail_df.iloc[0]["TOP_RETURN_REASON"] if not returns_detail_df.empty else "N/A"

            # Find most impactful reason
            if not has_error(returns_by_reason) and not returns_by_reason.empty:
                biggest_reason = returns_by_reason.iloc[0]["TOP_RETURN_REASON"]
                biggest_reason_margin = int(returns_by_reason.iloc[0]["MARGIN_LOST"])
            else:
                biggest_reason = "N/A"
                biggest_reason_margin = 0

            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #0f2027 0%, #1a2332 50%, #0d1b2a 100%);
                        border:1px solid #01b8fb; border-radius:10px; padding:14px 18px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; margin-bottom:6px;">
                    <span style="font-size:1rem; margin-right:8px;">🧠</span>
                    <span style="font-size:0.8rem; font-weight:700; color:#01b8fb; text-transform:uppercase; letter-spacing:0.05em;">
                        AI Returns Intelligence
                    </span>
                </div>
                <p style="color:#ecf6fd; font-size:0.84rem; line-height:1.5; margin:0 0 8px 0;">
                    <b>{total_returns}</b> returns across <b>{int(rk.TOTAL_RETURN_SKUS)}</b> SKUs eroding
                    <span style="color:#fbbf24;font-weight:600;">${total_margin_lost:,}</span> in margin.
                    Average return rate is <b>{avg_rate}%</b>.
                    <span style="color:#fbbf24;font-weight:600;">{skus_flagged} SKUs</span> flagged for rationalization — 
                    <span style="color:#4ade80;font-weight:600;">${recoverable:,}</span> margin recoverable if addressed.
                </p>
                <div style="display:flex;gap:16px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:200px;background:#1c1007;border:1px solid #92400e;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#fbbf24;font-weight:700;margin:0;text-transform:uppercase;">🚨 Biggest Margin Bleeder</p>
                        <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{worst_sku}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">-${worst_margin:,} margin lost · Reason: {top_reason}</p>
                    </div>
                    <div style="flex:1;min-width:200px;background:#1c1007;border:1px solid #92400e;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#fbbf24;font-weight:700;margin:0;text-transform:uppercase;">⚠ Top Return Driver</p>
                        <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{biggest_reason}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">${biggest_reason_margin:,} margin impact — Fix to reduce returns by ~40%</p>
                    </div>
                    <div style="flex:1;min-width:200px;background:#0d2818;border:1px solid #166534;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#4ade80;font-weight:700;margin:0;text-transform:uppercase;">💰 Recoverable Margin</p>
                        <p style="font-size:1.1rem;color:#ecf6fd;margin:2px 0;font-weight:700;">${recoverable:,}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">From {skus_flagged} flagged SKUs — rationalize or fix root causes</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ─── KPI ROW ───
        if not has_error(returns_kpi_df):
            rk = returns_kpi_df.iloc[0]
            ret_kpi_cols = st.columns(4)
            with ret_kpi_cols[0]:
                render_kpi("TOTAL RETURNS", str(int(rk.TOTAL_RETURNS)), f"Across {int(rk.TOTAL_RETURN_SKUS)} SKUs", "down")
            with ret_kpi_cols[1]:
                render_kpi("MARGIN EROSION", f"${int(rk.TOTAL_MARGIN_LOST):,}", f"${int(rk.TOTAL_REFUNDS):,} total refunds", "down")
            with ret_kpi_cols[2]:
                render_kpi("AVG RETURN RATE", f"{float(rk.AVG_RETURN_RATE)}%", "Per SKU average", "down" if float(rk.AVG_RETURN_RATE) > 1 else "up")
            with ret_kpi_cols[3]:
                render_kpi("RECOVERABLE MARGIN", f"${int(rk.RECOVERABLE_MARGIN):,}", f"{int(rk.SKUS_TO_RATIONALIZE)} SKUs to fix/remove", "up")

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── CHARTS: Margin Impact by Category + Return Reason Breakdown ───
        chart_c1, chart_c2 = st.columns(2)

        with chart_c1:
            st.markdown("**Margin Impact by Category** — _Where the $ is being lost_")
            if not has_error(returns_by_category) and not returns_by_category.empty:
                st.bar_chart(returns_by_category.set_index("CATEGORY")["MARGIN_LOST"])

        with chart_c2:
            st.markdown("**Return Reason Breakdown** — _Root causes by margin impact_")
            if not has_error(returns_by_reason) and not returns_by_reason.empty:
                st.bar_chart(returns_by_reason.set_index("TOP_RETURN_REASON")["MARGIN_LOST"])

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── QUICK WINS ───
        st.markdown("**Quick Wins** — _Top 3 SKUs where fixing the issue recovers the most margin_")
        if not has_error(returns_detail_df) and not returns_detail_df.empty:
            quick_wins = returns_detail_df[returns_detail_df["RATIONALIZATION_FLAG"] == True].head(3)
            if not quick_wins.empty:
                qw_cols = st.columns(len(quick_wins))
                action_map = {
                    "VENDOR_RMA": "Initiate vendor return & negotiate credit",
                    "IMPROVE_LISTING": "Update product images & description accuracy",
                    "QUALITY_REVIEW": "Escalate to QA for defect investigation",
                    "DISCONTINUE": "Remove from assortment & liquidate remaining stock"
                }
                for idx, row in quick_wins.iterrows():
                    with qw_cols[list(quick_wins.index).index(idx)]:
                        action_text = action_map.get(row["RECOMMENDED_ACTION"], row["RECOMMENDED_ACTION"])
                        st.markdown(f"""
                        <div style="background:#0a1a3a;border:1px solid #1a3a5c;border-top:3px solid #4ade80;border-radius:8px;padding:10px;text-align:center;">
                            <p style="font-size:0.72rem;font-weight:700;color:#4ade80;margin:0;">SAVE ${row['MARGIN_LOST']:,}</p>
                            <p style="font-size:0.78rem;font-weight:700;color:#ecf6fd;margin:4px 0;">{row['PRODUCT_NAME'][:30]}</p>
                            <p style="font-size:0.68rem;color:#8ec9f5;margin:2px 0;">{row['TOTAL_RETURNS']} returns · {row['RETURN_RATE_PCT']}% rate</p>
                            <p style="font-size:0.68rem;color:#fbbf24;margin:2px 0;">Reason: {row['TOP_RETURN_REASON']}</p>
                            <p style="font-size:0.65rem;color:#60a5fa;margin:4px 0 0 0;font-style:italic;">{action_text}</p>
                        </div>
                        """, unsafe_allow_html=True)

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── SKU DECISION BOARD ───
        st.markdown("**SKU Decision Board** — _Sorted by margin impact (highest loss first)_")
        st.markdown("""<div style="font-size:0.65rem;color:#64748b;margin-bottom:6px;line-height:1.6;">
            <b style="color:#8ec9f5;">Column Guide:</b>
            <b>Margin Lost ($)</b> = Total profit erosion from returns |
            <b>Return Rate %</b> = Returns as % of units sold |
            <b>Avg Days</b> = Average days between purchase and return |
            <b>Flagged</b> = AI recommends rationalization |
            <b>Action</b> = Recommended next step
        </div>""", unsafe_allow_html=True)

        if not has_error(returns_detail_df) and not returns_detail_df.empty:
            filt_c1, filt_c2, filt_c3 = st.columns(3)
            with filt_c1:
                ret_brand_filter = st.selectbox("Brand", ["All Brands"] + sorted(returns_detail_df["BRAND"].dropna().unique().tolist()), key="ret_brand_filter")
            with filt_c2:
                ret_cat_filter = st.selectbox("Category", ["All Categories"] + sorted(returns_detail_df["CATEGORY"].dropna().unique().tolist()), key="ret_cat_filter")
            with filt_c3:
                ret_flag_filter = st.selectbox("Status", ["All", "Flagged for Rationalization", "Not Flagged"], key="ret_flag_filter")

            filtered_ret = returns_detail_df.copy()
            if ret_brand_filter != "All Brands":
                filtered_ret = filtered_ret[filtered_ret["BRAND"] == ret_brand_filter]
            if ret_cat_filter != "All Categories":
                filtered_ret = filtered_ret[filtered_ret["CATEGORY"] == ret_cat_filter]
            if ret_flag_filter == "Flagged for Rationalization":
                filtered_ret = filtered_ret[filtered_ret["RATIONALIZATION_FLAG"] == True]
            elif ret_flag_filter == "Not Flagged":
                filtered_ret = filtered_ret[filtered_ret["RATIONALIZATION_FLAG"] == False]

            # Map actions to descriptive text
            ret_action_map = {
                "VENDOR_RMA": "Initiate vendor return & negotiate credit",
                "IMPROVE_LISTING": "Update product images & description",
                "QUALITY_REVIEW": "Escalate to QA for defect review",
                "DISCONTINUE": "Remove from assortment & liquidate"
            }
            filtered_ret["ACTION_DESC"] = filtered_ret["RECOMMENDED_ACTION"].map(ret_action_map).fillna(filtered_ret["RECOMMENDED_ACTION"])

            display_ret_df = filtered_ret[["PRODUCT_NAME", "BRAND", "MARGIN_LOST", "RETURN_RATE_PCT", "AVG_DAYS", "TOP_RETURN_REASON", "RATIONALIZATION_FLAG", "ACTION_DESC"]].rename(columns={
                "PRODUCT_NAME": "Product",
                "BRAND": "Brand",
                "MARGIN_LOST": "Margin Lost ($)",
                "RETURN_RATE_PCT": "Return Rate %",
                "AVG_DAYS": "Avg Days",
                "TOP_RETURN_REASON": "Reason",
                "RATIONALIZATION_FLAG": "Flagged",
                "ACTION_DESC": "Recommended Action"
            })

            st.caption(f"Showing {len(display_ret_df)} SKUs — sorted by margin impact")
            render_table(display_ret_df.reset_index(drop=True))
        else:
            st.info("No returns data available.")


with tab_main_health:
    # ─── HEALTH CHECK VIEW ───

    # Load category performance
    cat_perf_df = run_sql(f"""
        SELECT CATEGORY, TOTAL_ACTIVE_SKUS_IN_CATEGORY, COUNT_OVERPRICED_SKUS,
               COUNT_UNDERPRICED_SKUS, COUNT_AT_PRICE_PARITY_SKUS,
               COUNT_OUT_OF_STOCK_SKUS, COUNT_LOW_STOCK_SKUS,
               ROUND(AVERAGE_MARGIN_PERCENTAGE, 1) AS AVG_MARGIN,
               ROUND(TOTAL_INVENTORY_RETAIL_VALUE_USD, 0) AS INV_VALUE,
               COUNT_SKUS_NEEDING_PRICE_ACTION, COUNT_SKUS_NEEDING_REPLENISHMENT
        FROM {SCHEMA}.GOLD_CATEGORY_PERFORMANCE_SUMMARY
        ORDER BY TOTAL_INVENTORY_RETAIL_VALUE_USD DESC
    """)

    # Load returns by category for health scoring
    ret_cat_df = run_sql(f"""
        SELECT CATEGORY, SUM(TOTAL_RETURNS) AS RETURNS, ROUND(SUM(TOTAL_MARGIN_LOST_USD), 0) AS MARGIN_LOST
        FROM {SCHEMA}.GOLD_RETURNS_MARGIN_ANALYSIS
        GROUP BY CATEGORY
    """)

    # Load stock urgency
    stock_urgency_df = run_sql(f"""
        SELECT PRODUCT_NAME, BRAND, CATEGORY, CURRENT_STOCK_LEVEL, STOCK_AVAILABILITY_STATUS,
               ROUND(OUR_CURRENT_PRICE * CURRENT_STOCK_LEVEL, 0) AS STOCK_VALUE,
               CORTEX_AI_RECOMMENDED_ACTION_TYPE AS AI_ACTION
        FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
        WHERE REQUIRES_REPLENISHMENT_ACTION = TRUE
        ORDER BY OUR_CURRENT_PRICE * CURRENT_STOCK_LEVEL ASC
        LIMIT 10
    """)

    if not has_error(cat_perf_df) and not cat_perf_df.empty:
        total_categories = len(cat_perf_df)
        total_skus = int(cat_perf_df["TOTAL_ACTIVE_SKUS_IN_CATEGORY"].sum())
        total_overpriced = int(cat_perf_df["COUNT_OVERPRICED_SKUS"].sum())
        total_underpriced = int(cat_perf_df["COUNT_UNDERPRICED_SKUS"].sum())
        total_out_of_stock = int(cat_perf_df["COUNT_OUT_OF_STOCK_SKUS"].sum())
        total_low_stock = int(cat_perf_df["COUNT_LOW_STOCK_SKUS"].sum())
        total_stock_issues = total_out_of_stock + total_low_stock
        avg_margin_all = round(cat_perf_df["AVG_MARGIN"].mean(), 1)
        total_needing_replenishment = int(cat_perf_df["COUNT_SKUS_NEEDING_REPLENISHMENT"].sum())
        total_needing_price = int(cat_perf_df["COUNT_SKUS_NEEDING_PRICE_ACTION"].sum())

        # Calculate health scores per category
        def calc_health_score(row):
            margin_score = min(float(row["AVG_MARGIN"]) / 50 * 40, 40)  # max 40 pts
            stock_issues = int(row["COUNT_OUT_OF_STOCK_SKUS"]) + int(row["COUNT_LOW_STOCK_SKUS"])
            stock_score = max(30 - stock_issues * 5, 0)  # max 30 pts
            overpriced_pct = int(row["COUNT_OVERPRICED_SKUS"]) / max(int(row["TOTAL_ACTIVE_SKUS_IN_CATEGORY"]), 1) * 100
            price_score = max(30 - overpriced_pct * 0.5, 0)  # max 30 pts
            return min(round(margin_score + stock_score + price_score), 100)

        cat_perf_df["HEALTH_SCORE"] = cat_perf_df.apply(calc_health_score, axis=1)

        # Identify weakest & strongest
        weakest_cat = cat_perf_df.loc[cat_perf_df["HEALTH_SCORE"].idxmin()]
        strongest_cat = cat_perf_df.loc[cat_perf_df["HEALTH_SCORE"].idxmax()]

        # ─── AI HEALTH INTELLIGENCE BANNER (3 cards) ───
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #0f2027 0%, #1a2332 50%, #0d1b2a 100%);
                    border:1px solid #01b8fb; border-radius:10px; padding:14px 18px; margin-bottom:10px;">
            <div style="display:flex; align-items:center; margin-bottom:6px;">
                <span style="font-size:1rem; margin-right:8px;">🧠</span>
                <span style="font-size:0.8rem; font-weight:700; color:#01b8fb; text-transform:uppercase; letter-spacing:0.05em;">
                    AI Category Health Intelligence
                </span>
            </div>
            <p style="color:#ecf6fd; font-size:0.84rem; line-height:1.5; margin:0 0 8px 0;">
                Monitoring <b>{total_categories}</b> categories with <b>{total_skus}</b> active SKUs.
                Average margin <b>{avg_margin_all}%</b>.
                <span style="color:#fbbf24;font-weight:600;">{total_overpriced} overpriced</span>,
                <span style="color:#fbbf24;font-weight:600;">{total_stock_issues} availability issues</span>,
                <span style="color:#4ade80;font-weight:600;">{total_needing_replenishment} need replenishment</span>.
            </p>
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                <div style="flex:1;min-width:200px;background:#1c1007;border:1px solid #92400e;border-radius:6px;padding:8px 12px;">
                    <p style="font-size:0.68rem;color:#fbbf24;font-weight:700;margin:0;text-transform:uppercase;">🚨 Weakest Category</p>
                    <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{weakest_cat['CATEGORY']} (Score: {int(weakest_cat['HEALTH_SCORE'])}/100)</p>
                    <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">{int(weakest_cat['COUNT_OVERPRICED_SKUS'])} overpriced · {int(weakest_cat['COUNT_OUT_OF_STOCK_SKUS']) + int(weakest_cat['COUNT_LOW_STOCK_SKUS'])} stock issues · {weakest_cat['AVG_MARGIN']}% margin</p>
                </div>
                <div style="flex:1;min-width:200px;background:#0d2818;border:1px solid #166534;border-radius:6px;padding:8px 12px;">
                    <p style="font-size:0.68rem;color:#4ade80;font-weight:700;margin:0;text-transform:uppercase;">✓ Strongest Category</p>
                    <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{strongest_cat['CATEGORY']} (Score: {int(strongest_cat['HEALTH_SCORE'])}/100)</p>
                    <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">{strongest_cat['AVG_MARGIN']}% margin · {int(strongest_cat['COUNT_AT_PRICE_PARITY_SKUS'])} at parity</p>
                </div>
                <div style="flex:1;min-width:200px;background:#030c25;border:1px solid #1e40af;border-radius:6px;padding:8px 12px;">
                    <p style="font-size:0.68rem;color:#60a5fa;font-weight:700;margin:0;text-transform:uppercase;">💡 Priority Actions</p>
                    <p style="font-size:0.72rem;color:#ecf6fd;margin:2px 0;line-height:1.4;">Replenish {total_needing_replenishment} SKUs · Reprice {total_needing_price} SKUs · Fix {total_out_of_stock} out-of-stock items</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ─── KPI ROW ───
        hk_cols = st.columns(4)
        with hk_cols[0]:
            render_kpi("ACTIVE SKUs", str(total_skus), f"Across {total_categories} categories", "up")
        with hk_cols[1]:
            render_kpi("AVG MARGIN", f"{avg_margin_all}%", "Portfolio average", "up" if avg_margin_all > 30 else "down")
        with hk_cols[2]:
            render_kpi("AVAILABILITY RISK", f"{total_stock_issues} SKUs", f"{total_out_of_stock} OOS + {total_low_stock} Low", "down" if total_stock_issues > 10 else "up")
        with hk_cols[3]:
            render_kpi("PRICING ALERTS", f"{total_needing_price} SKUs", f"{total_overpriced} overpriced vs market", "down" if total_overpriced > 10 else "up")

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── CATEGORY HEALTH SCORECARDS (with scores) ───
        st.markdown("**Category Health Scorecards** — _Score based on margin, stock availability, and pricing competitiveness_")
        cat_cols = st.columns(len(cat_perf_df))
        for idx, row in cat_perf_df.iterrows():
            with cat_cols[idx]:
                score = int(row["HEALTH_SCORE"])
                total_skus_cat = int(row["TOTAL_ACTIVE_SKUS_IN_CATEGORY"])
                stock_issues_cat = int(row["COUNT_OUT_OF_STOCK_SKUS"]) + int(row["COUNT_LOW_STOCK_SKUS"])
                margin = float(row["AVG_MARGIN"])

                if score >= 70:
                    health_color = "#4ade80"
                    health_label = "HEALTHY"
                elif score >= 50:
                    health_color = "#fbbf24"
                    health_label = "WATCH"
                else:
                    health_color = "#fbbf24"
                    health_label = "AT RISK"

                # Determine action
                if stock_issues_cat >= 4:
                    action_text = "Prioritize replenishment"
                elif int(row["COUNT_OVERPRICED_SKUS"]) > total_skus_cat * 0.5:
                    action_text = "Review pricing strategy"
                elif margin < 30:
                    action_text = "Improve margins"
                else:
                    action_text = "Monitor & maintain"

                cat_returns = 0
                if not has_error(ret_cat_df) and not ret_cat_df.empty:
                    cat_match = ret_cat_df[ret_cat_df["CATEGORY"] == row["CATEGORY"]]
                    if not cat_match.empty:
                        cat_returns = int(cat_match.iloc[0]["RETURNS"])

                # Progress bar width
                bar_width = score

                st.markdown(f"""
                <div style="background:#0a1a3a;border:1px solid #1a3a5c;border-radius:8px;padding:12px;text-align:center;">
                    <p style="font-size:0.68rem;font-weight:700;color:{health_color};margin:0;">{health_label}</p>
                    <p style="font-size:0.88rem;font-weight:700;color:#ecf6fd;margin:2px 0;">{row['CATEGORY']}</p>
                    <div style="background:#030c25;border-radius:4px;height:6px;margin:6px 0;">
                        <div style="background:{health_color};width:{bar_width}%;height:6px;border-radius:4px;"></div>
                    </div>
                    <p style="font-size:0.72rem;font-weight:700;color:{health_color};margin:2px 0;">{score}/100</p>
                    <p style="font-size:0.65rem;color:#8ec9f5;margin:2px 0;">{total_skus_cat} SKUs · {margin}% margin</p>
                    <p style="font-size:0.65rem;color:#8ec9f5;margin:2px 0;">{int(row['COUNT_OVERPRICED_SKUS'])} overpriced · {stock_issues_cat} stock risk</p>
                    <p style="font-size:0.65rem;color:#8ec9f5;margin:2px 0;">{cat_returns} returns</p>
                    <p style="font-size:0.62rem;color:#60a5fa;margin:4px 0 0 0;font-style:italic;">{action_text}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── CROSS-CATEGORY EXECUTIVE SCORECARD ───
        st.markdown("**Executive Scorecard** — _At-a-glance comparison across all categories_")
        exec_data = []
        for _, row in cat_perf_df.iterrows():
            cat_ret = 0
            cat_margin_lost = 0
            if not has_error(ret_cat_df) and not ret_cat_df.empty:
                cat_match = ret_cat_df[ret_cat_df["CATEGORY"] == row["CATEGORY"]]
                if not cat_match.empty:
                    cat_ret = int(cat_match.iloc[0]["RETURNS"])
                    cat_margin_lost = int(cat_match.iloc[0]["MARGIN_LOST"])
            exec_data.append({
                "Category": row["CATEGORY"],
                "Health Score": int(row["HEALTH_SCORE"]),
                "Margin %": float(row["AVG_MARGIN"]),
                "Stock Risk": int(row["COUNT_OUT_OF_STOCK_SKUS"]) + int(row["COUNT_LOW_STOCK_SKUS"]),
                "Price Risk": int(row["COUNT_OVERPRICED_SKUS"]),
                "Returns": cat_ret,
                "Margin Lost ($)": cat_margin_lost,
                "Inventory ($)": int(row["INV_VALUE"])
            })
        exec_df = pd.DataFrame(exec_data).sort_values("Health Score", ascending=True)
        render_table(exec_df.reset_index(drop=True))

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── COMPETITIVE POSITION + TOP ACTIONS (side by side) ───
        col_comp, col_actions = st.columns(2)

        with col_comp:
            st.markdown("**Competitive Position** — _Pricing stance vs market_")
            comp_data = []
            for _, row in cat_perf_df.iterrows():
                total_cat_skus = int(row["TOTAL_ACTIVE_SKUS_IN_CATEGORY"])
                comp_data.append({
                    "Category": row["CATEGORY"],
                    "Overpriced": round(int(row["COUNT_OVERPRICED_SKUS"]) / max(total_cat_skus, 1) * 100, 0),
                    "At Parity": round(int(row["COUNT_AT_PRICE_PARITY_SKUS"]) / max(total_cat_skus, 1) * 100, 0),
                    "Underpriced": round(int(row["COUNT_UNDERPRICED_SKUS"]) / max(total_cat_skus, 1) * 100, 0),
                })
            comp_chart_df = pd.DataFrame(comp_data).set_index("Category")
            st.bar_chart(comp_chart_df, height=220)

        with col_actions:
            st.markdown("**Top Actions Required** — _Most urgent items_")
            actions_list = []
            if total_out_of_stock > 0:
                actions_list.append(("🔴", "CRITICAL", f"Replenish {total_out_of_stock} out-of-stock SKUs immediately"))
            if total_needing_price > 5:
                actions_list.append(("🟠", "HIGH", f"Review pricing on {total_needing_price} misaligned SKUs"))
            if total_low_stock > 0:
                actions_list.append(("🟡", "MEDIUM", f"Reorder {total_low_stock} low-stock SKUs"))
            if not has_error(ret_cat_df) and not ret_cat_df.empty:
                worst_ret_cat = ret_cat_df.loc[ret_cat_df["MARGIN_LOST"].idxmax()]
                actions_list.append(("🟠", "HIGH", f"Returns in {worst_ret_cat['CATEGORY']} — ${int(worst_ret_cat['MARGIN_LOST']):,} lost"))
            actions_list.append(("🟡", "MEDIUM", f"Deep-dive {weakest_cat['CATEGORY']} (score {int(weakest_cat['HEALTH_SCORE'])}/100)"))

            for icon, severity, action in actions_list[:5]:
                sev_color = "#fbbf24" if severity == "CRITICAL" else ("#fbbf24" if severity == "HIGH" else "#60a5fa")
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:8px;padding:5px 10px;margin:3px 0;background:#0a1a3a;border-radius:6px;border-left:3px solid {sev_color};">
                    <span style="font-size:0.82rem;">{icon}</span>
                    <span style="font-size:0.65rem;font-weight:700;color:{sev_color};min-width:55px;">{severity}</span>
                    <span style="font-size:0.72rem;color:#ecf6fd;">{action}</span>
                </div>
                """, unsafe_allow_html=True)

        # ─── REPLENISHMENT (TOGGLE) ───
        show_replenish = st.checkbox("📦 Replenishment Priority Board — Click to view SKUs needing restock", key="show_replenish_board")
        if show_replenish:
            if not has_error(stock_urgency_df) and not stock_urgency_df.empty:
                display_stock = stock_urgency_df.rename(columns={
                    "PRODUCT_NAME": "Product",
                    "BRAND": "Brand",
                    "CATEGORY": "Category",
                    "CURRENT_STOCK_LEVEL": "Stock Level",
                    "STOCK_AVAILABILITY_STATUS": "Status",
                    "STOCK_VALUE": "Stock Value ($)",
                    "AI_ACTION": "AI Action"
                })
                render_table(display_stock.reset_index(drop=True))
            else:
                st.markdown('<p style="font-size:0.78rem;color:#4ade80;">All SKUs adequately stocked.</p>', unsafe_allow_html=True)

with tab_main_sku:
    # ─── SKU DEEP DIVE ───

    # Load SKU list for selector
    sku_list_df = run_sql(f"""
        SELECT SKU_ID, PRODUCT_NAME, BRAND, CATEGORY
        FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
        ORDER BY PRODUCT_NAME
    """)

    if not has_error(sku_list_df) and not sku_list_df.empty:
        sku_options = [f"{row['SKU_ID']} — {row['PRODUCT_NAME']}" for _, row in sku_list_df.iterrows()]
        selected_sku_label = st.selectbox("Select a SKU to analyze", sku_options, key="sku_deep_dive_select")
        selected_sku_id = selected_sku_label.split(" — ")[0]

        # Load SKU details
        sku_detail = run_sql(f"""
            SELECT SKU_ID, PRODUCT_NAME, BRAND, CATEGORY, SUBCATEGORY,
                   ROUND(OUR_CURRENT_PRICE, 2) AS OUR_PRICE, ROUND(OUR_COST_PRICE, 2) AS COST,
                   ROUND(OUR_MARGIN_PERCENTAGE, 1) AS MARGIN_PCT, ROUND(OUR_MARGIN_AMOUNT_USD, 2) AS MARGIN_USD,
                   CURRENT_STOCK_LEVEL, STOCK_AVAILABILITY_STATUS, ESTIMATED_DAYS_UNTIL_STOCKOUT,
                   PRIMARY_COMPETITOR_NAME, ROUND(PRIMARY_COMPETITOR_PRICE, 2) AS PRIMARY_COMP_PRICE,
                   ROUND(PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT, 1) AS GAP_PCT,
                   OVERALL_COMPETITIVE_POSITIONING_STATUS, NUMBER_OF_COMPETITORS_FOUND,
                   CORTEX_AI_RECOMMENDATION_SUMMARY, CORTEX_AI_RECOMMENDED_ACTION_TYPE,
                   REQUIRES_IMMEDIATE_PRICE_REVIEW, REQUIRES_REPLENISHMENT_ACTION
            FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
            WHERE SKU_ID = '{selected_sku_id}'
        """)

        if not has_error(sku_detail) and not sku_detail.empty:
            s = sku_detail.iloc[0]

            # ─── AI INSIGHT BANNER (3 cards) ───
            status_color = "#fbbf24" if s["OVERALL_COMPETITIVE_POSITIONING_STATUS"] == "OVERPRICED" else ("#4ade80" if s["OVERALL_COMPETITIVE_POSITIONING_STATUS"] == "UNDERPRICED" else "#fbbf24")
            stock_color = "#fbbf24" if s["STOCK_AVAILABILITY_STATUS"] == "OUT_OF_STOCK" else ("#fbbf24" if s["STOCK_AVAILABILITY_STATUS"] == "LOW_STOCK" else "#4ade80")
            ai_summary = s["CORTEX_AI_RECOMMENDATION_SUMMARY"] if s["CORTEX_AI_RECOMMENDATION_SUMMARY"] else "No recommendation available."
            ai_action = s["CORTEX_AI_RECOMMENDED_ACTION_TYPE"] or "MONITOR"

            # Stock forecast
            days_out = int(s['ESTIMATED_DAYS_UNTIL_STOCKOUT']) if pd.notna(s['ESTIMATED_DAYS_UNTIL_STOCKOUT']) else None
            if days_out and days_out < 7:
                stock_urgency = "CRITICAL — Reorder immediately"
                stock_urgency_color = "#fbbf24"
            elif days_out and days_out < 21:
                stock_urgency = "WARNING — Reorder soon"
                stock_urgency_color = "#fbbf24"
            elif days_out:
                stock_urgency = "HEALTHY — Adequate supply"
                stock_urgency_color = "#4ade80"
            else:
                stock_urgency = "Unknown"
                stock_urgency_color = "#64748b"

            # Action mapping
            action_map = {
                "REPRICE": "Adjust price to match market positioning",
                "REPLENISH": "Place reorder to prevent stockout",
                "MONITOR": "Continue monitoring — no action needed",
                "ESCALATE": "Escalate to senior review for decision"
            }
            action_text = action_map.get(ai_action, ai_action)

            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #0f2027 0%, #1a2332 50%, #0d1b2a 100%);
                        border:1px solid #01b8fb; border-radius:10px; padding:14px 18px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; margin-bottom:6px;">
                    <span style="font-size:1rem; margin-right:8px;">🧠</span>
                    <span style="font-size:0.8rem; font-weight:700; color:#01b8fb; text-transform:uppercase; letter-spacing:0.05em;">
                        AI SKU Diagnosis — {s['PRODUCT_NAME']}
                    </span>
                </div>
                <p style="color:#ecf6fd; font-size:0.84rem; line-height:1.5; margin:0 0 8px 0;">
                    <b>{s['BRAND']}</b> · {s['CATEGORY']} · {s['CURRENT_STOCK_LEVEL']} units in stock ·
                    Pricing: <span style="color:{status_color};font-weight:600;">{s['OVERALL_COMPETITIVE_POSITIONING_STATUS'].replace('_', ' ')}</span> ·
                    {s['NUMBER_OF_COMPETITORS_FOUND']} competitors tracked
                </p>
                <div style="display:flex;gap:16px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:180px;background:#030c25;border:1px solid #1e40af;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#60a5fa;font-weight:700;margin:0;text-transform:uppercase;">🎯 Pricing Position</p>
                        <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">${s['OUR_PRICE']} vs ${s['PRIMARY_COMP_PRICE'] if pd.notna(s['PRIMARY_COMP_PRICE']) else 'N/A'}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">Gap: <span style="color:{status_color};font-weight:600;">{s['GAP_PCT']}%</span> vs {s['PRIMARY_COMPETITOR_NAME'] or 'N/A'}</p>
                    </div>
                    <div style="flex:1;min-width:180px;background:#030c25;border:1px solid {'#92400e' if stock_urgency_color == '#fbbf24' else '#1e40af'};border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:{stock_urgency_color};font-weight:700;margin:0;text-transform:uppercase;">📦 Stock Forecast</p>
                        <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{f'{days_out} days until stockout' if days_out else 'N/A'}</p>
                        <p style="font-size:0.7rem;color:{stock_urgency_color};margin:0;">{stock_urgency}</p>
                    </div>
                    <div style="flex:1;min-width:180px;background:#0d2818;border:1px solid #166534;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#4ade80;font-weight:700;margin:0;text-transform:uppercase;">💡 AI Action</p>
                        <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{ai_action}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">{action_text}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ─── KPI ROW ───
            kpi_cols = st.columns(4)
            with kpi_cols[0]:
                render_kpi("OUR PRICE", f"${s['OUR_PRICE']}", f"Cost: ${s['COST']}", "up")
            with kpi_cols[1]:
                render_kpi("MARGIN", f"{s['MARGIN_PCT']}%", f"${s['MARGIN_USD']} per unit", "up" if s['MARGIN_PCT'] > 25 else "down")
            with kpi_cols[2]:
                comp_price_display = f"${s['PRIMARY_COMP_PRICE']}" if pd.notna(s['PRIMARY_COMP_PRICE']) else "N/A"
                render_kpi("COMPETITOR PRICE", comp_price_display, f"{s['PRIMARY_COMPETITOR_NAME'] or 'N/A'} · Gap {s['GAP_PCT']}%", "down" if s['GAP_PCT'] and s['GAP_PCT'] > 0 else "up")
            with kpi_cols[3]:
                days_display = f"{days_out} days" if days_out else "N/A"
                render_kpi("STOCK LEVEL", str(s['CURRENT_STOCK_LEVEL']), f"~{days_display} until stockout", "up" if s['CURRENT_STOCK_LEVEL'] > 50 else "down")

            st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

            # ─── EXECUTE ACTION ───
            st.markdown(f"**Execute Action** — _AI recommends: **{ai_action}** · You decide._")

            action_cols = st.columns(4)
            with action_cols[0]:
                reprice_btn = st.button("💲 REPRICE", use_container_width=True, key="action_reprice")
            with action_cols[1]:
                replenish_btn = st.button("📦 REPLENISH", use_container_width=True, key="action_replenish")
            with action_cols[2]:
                monitor_btn = st.button("👁️ MONITOR", use_container_width=True, key="action_monitor")
            with action_cols[3]:
                escalate_btn = st.button("🚨 ESCALATE", use_container_width=True, key="action_escalate")

            # Determine which action was clicked
            clicked_action = None
            if reprice_btn:
                clicked_action = "REPRICE"
            elif replenish_btn:
                clicked_action = "REPLENISH"
            elif monitor_btn:
                clicked_action = "MONITOR"
            elif escalate_btn:
                clicked_action = "ESCALATE"

            if clicked_action:
                st.session_state["pending_action"] = clicked_action
                st.session_state["pending_sku"] = selected_sku_id

            # Show confirmation if action is pending
            pending = st.session_state.get("pending_action")
            pending_sku = st.session_state.get("pending_sku")
            if pending and pending_sku == selected_sku_id:
                action_details = {
                    "REPRICE": {"desc": f"Adjust price of {s['PRODUCT_NAME']} to match competitor ({s['PRIMARY_COMPETITOR_NAME']}: ${s['PRIMARY_COMP_PRICE'] if pd.notna(s['PRIMARY_COMP_PRICE']) else 'N/A'})", "color": "#60a5fa", "new_val": str(s['PRIMARY_COMP_PRICE']) if pd.notna(s['PRIMARY_COMP_PRICE']) else ""},
                    "REPLENISH": {"desc": f"Reorder {s['PRODUCT_NAME']} — current stock: {s['CURRENT_STOCK_LEVEL']} units", "color": "#4ade80", "new_val": "100"},
                    "MONITOR": {"desc": f"Add {s['PRODUCT_NAME']} to watchlist for daily monitoring", "color": "#fbbf24", "new_val": ""},
                    "ESCALATE": {"desc": f"Flag {s['PRODUCT_NAME']} for senior review — gap {s['GAP_PCT']}% vs market", "color": "#fbbf24", "new_val": ""},
                }
                detail = action_details[pending]

                st.markdown(f"""
                <div style="background:#0a1a3a;border:1px solid {detail['color']};border-radius:8px;padding:12px;margin-top:8px;">
                    <p style="font-size:0.78rem;font-weight:700;color:{detail['color']};margin:0;">Confirm: {pending}</p>
                    <p style="font-size:0.76rem;color:#ecf6fd;margin:4px 0;">{detail['desc']}</p>
                    <p style="font-size:0.68rem;color:#8ec9f5;margin:2px 0;">SKU: {selected_sku_id} · Action will be logged to audit trail.</p>
                </div>
                """, unsafe_allow_html=True)

                confirm_cols = st.columns([3, 2, 3])
                with confirm_cols[1]:
                    if st.button("✓ Confirm Execution", type="primary", use_container_width=True, key="confirm_action"):
                        try:
                            reason = f"User-initiated {pending} from SKU Deep Dive"
                            new_val = detail["new_val"]
                            session = get_session()
                            session.sql(f"""
                                CALL {SCHEMA}.EXECUTE_SKU_ACTION('{pending}', '{selected_sku_id}', '{reason}', '{new_val}')
                            """).collect()
                            st.session_state["action_success"] = f"✓ {pending} executed successfully for {selected_sku_id}"
                            st.session_state["pending_action"] = None
                            st.session_state["pending_sku"] = None
                            st.rerun()
                        except Exception as e:
                            st.session_state["action_success"] = None
                            st.markdown(f"""
                            <div style="background:#1c1007;border:1px solid #92400e;border-radius:8px;padding:10px;margin-top:6px;text-align:center;">
                                <p style="font-size:0.78rem;color:#fbbf24;font-weight:700;margin:0;">Execution failed</p>
                                <p style="font-size:0.68rem;color:#8ec9f5;margin:2px 0;">{str(e)[:100]}</p>
                            </div>
                            """, unsafe_allow_html=True)

            # Show persistent success message
            if st.session_state.get("action_success"):
                st.markdown(f"""
                <div style="background:#0d2818;border:1px solid #166534;border-radius:8px;padding:10px;margin-top:6px;text-align:center;">
                    <p style="font-size:0.78rem;color:#4ade80;font-weight:700;margin:0;">{st.session_state['action_success']}</p>
                    <p style="font-size:0.68rem;color:#8ec9f5;margin:2px 0;">Logged to GOLD_ACTION_EXECUTION_AUDIT</p>
                </div>
                """, unsafe_allow_html=True)
                st.session_state["action_success"] = None

            st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

            # ─── SALES TREND + COMPETITOR CHART (side by side) ───
            col_sales, col_comp = st.columns(2)

            with col_sales:
                st.markdown("**📈 Weekly Sales Trend** — _Units sold over 13 weeks_")
                sales_df = run_sql(f"""
                    SELECT WEEK_START_DATE, UNITS_SOLD
                    FROM {SCHEMA}.SILVER_WEEKLY_SALES_CLEANSED
                    WHERE SKU_ID = '{selected_sku_id}'
                    ORDER BY WEEK_START_DATE
                """)
                if not has_error(sales_df) and not sales_df.empty:
                    sales_df["WEEK_START_DATE"] = pd.to_datetime(sales_df["WEEK_START_DATE"])
                    sales_df = sales_df.sort_values("WEEK_START_DATE").reset_index(drop=True)
                    sales_df["Week"] = sales_df["WEEK_START_DATE"].dt.strftime('%b %d')
                    chart_data = sales_df.set_index("Week")[["UNITS_SOLD"]]
                    st.line_chart(chart_data)
                else:
                    st.info("No sales data available for this SKU.")

            with col_comp:
                st.markdown("**🏪 Competitor Price Landscape**")
                comp_df = run_sql(f"""
                    SELECT COMPETITOR_NAME, ROUND(COMPETITOR_PRICE, 2) AS PRICE
                    FROM {SCHEMA}.SILVER_COMPETITOR_PRICE_ENRICHED
                    WHERE SKU_ID = '{selected_sku_id}'
                    ORDER BY COMPETITOR_PRICE
                """)
                if not has_error(comp_df) and not comp_df.empty:
                    our_row = pd.DataFrame({"COMPETITOR_NAME": ["** OUR PRICE **"], "PRICE": [s['OUR_PRICE']]})
                    chart_df = pd.concat([comp_df, our_row], ignore_index=True)
                    st.bar_chart(chart_df.set_index("COMPETITOR_NAME")["PRICE"], height=220)
                else:
                    st.info("No competitor pricing data available.")

            st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

            # ─── RETURNS + CATEGORY PEERS (side by side) ───
            col_returns, col_peers = st.columns(2)

            with col_returns:
                st.markdown("**🔄 Returns Analysis**")
                ret_df = run_sql(f"""
                    SELECT RETURN_REASON, COUNT(*) AS RETURNS, ROUND(SUM(MARGIN_LOST_USD), 0) AS MARGIN_LOST
                    FROM {SCHEMA}.SILVER_RETURNS_ENRICHED
                    WHERE SKU_ID = '{selected_sku_id}'
                    GROUP BY RETURN_REASON ORDER BY RETURNS DESC
                """)
                if not has_error(ret_df) and not ret_df.empty:
                    total_returns = int(ret_df["RETURNS"].sum())
                    total_margin_lost = int(ret_df["MARGIN_LOST"].sum())
                    top_reason = ret_df.iloc[0]["RETURN_REASON"]
                    st.markdown(f"""
                    <div style="background:#0a1a3a;border-radius:6px;padding:8px 12px;margin-bottom:6px;">
                        <span style="font-size:0.76rem;color:#fbbf24;font-weight:700;">{total_returns} returns</span>
                        <span style="font-size:0.72rem;color:#8ec9f5;"> · ${total_margin_lost:,} margin lost</span>
                        <span style="font-size:0.72rem;color:#8ec9f5;"> · Top reason: </span>
                        <span style="font-size:0.72rem;color:#fbbf24;font-weight:600;">{top_reason}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.bar_chart(ret_df.set_index("RETURN_REASON")["RETURNS"], height=180)
                else:
                    st.markdown('<p style="font-size:0.78rem;color:#4ade80;">No returns recorded for this SKU.</p>', unsafe_allow_html=True)

            with col_peers:
                st.markdown("**👥 Category Peers** — _Similar SKUs for comparison_")
                peers_df = run_sql(f"""
                    SELECT PRODUCT_NAME AS "Product",
                           ROUND(OUR_CURRENT_PRICE, 2) AS "Price ($)",
                           ROUND(OUR_MARGIN_PERCENTAGE, 1) AS "Margin %",
                           CURRENT_STOCK_LEVEL AS "Stock",
                           OVERALL_COMPETITIVE_POSITIONING_STATUS AS "Status"
                    FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
                    WHERE CATEGORY = '{s['CATEGORY']}' AND SKU_ID != '{selected_sku_id}'
                    ORDER BY ABS(OUR_CURRENT_PRICE - {s['OUR_PRICE']})
                    LIMIT 5
                """)
                if not has_error(peers_df) and not peers_df.empty:
                    render_table(peers_df.reset_index(drop=True), max_height="220px")
                else:
                    st.info("No peers found in this category.")
    else:
        st.info("No SKU data available.")

with tab_main_price:
    # ─── PRICE SIMULATION ───

    # Load all SKU data for simulation
    sim_base_df = run_sql(f"""
        SELECT SKU_ID, PRODUCT_NAME, BRAND, CATEGORY,
               OUR_CURRENT_PRICE, OUR_COST_PRICE, OUR_MARGIN_PERCENTAGE, OUR_MARGIN_AMOUNT_USD,
               PRIMARY_COMPETITOR_PRICE, PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT,
               OVERALL_COMPETITIVE_POSITIONING_STATUS, CURRENT_STOCK_LEVEL
        FROM {SCHEMA}.GOLD_SKU_PRICING_INTELLIGENCE
        ORDER BY CATEGORY, BRAND, PRODUCT_NAME
    """)

    if not has_error(sim_base_df) and not sim_base_df.empty:
        # ─── SCENARIO PRESETS ───
        st.markdown("**Scenario Presets** — _Quick simulations_")
        preset_cols = st.columns(4)
        with preset_cols[0]:
            if st.button("📊 Match Competitor", use_container_width=True, key="preset_match"):
                st.session_state["sim_preset"] = "match"
        with preset_cols[1]:
            if st.button("⚡ Undercut 5%", use_container_width=True, key="preset_undercut"):
                st.session_state["sim_preset"] = "undercut"
        with preset_cols[2]:
            if st.button("💰 Maximize Margin (+10%)", use_container_width=True, key="preset_margin"):
                st.session_state["sim_preset"] = "margin"
        with preset_cols[3]:
            if st.button("🔄 Reset to Current", use_container_width=True, key="preset_reset"):
                st.session_state["sim_preset"] = "reset"

        st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

        # ─── FILTER CONTROLS ───
        ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([2, 2, 3])
        with ctrl_c1:
            sim_categories = ["All Categories"] + sorted(sim_base_df["CATEGORY"].dropna().unique().tolist())
            sim_cat = st.selectbox("Category", sim_categories, key="sim_cat")
        with ctrl_c2:
            if sim_cat != "All Categories":
                brand_options = ["All Brands"] + sorted(sim_base_df[sim_base_df["CATEGORY"] == sim_cat]["BRAND"].dropna().unique().tolist())
            else:
                brand_options = ["All Brands"] + sorted(sim_base_df["BRAND"].dropna().unique().tolist())
            sim_brand = st.selectbox("Brand", brand_options, key="sim_brand")
        with ctrl_c3:
            # Determine default slider value from preset
            preset = st.session_state.get("sim_preset", "reset")
            default_val = 0
            if preset == "undercut":
                default_val = -5
            elif preset == "margin":
                default_val = 10
            price_change = st.slider("Price Change %", min_value=-30, max_value=30, value=default_val, step=1, key="sim_slider")

        # Apply filters
        sim_df = sim_base_df.copy()
        if sim_cat != "All Categories":
            sim_df = sim_df[sim_df["CATEGORY"] == sim_cat]
        if sim_brand != "All Brands":
            sim_df = sim_df[sim_df["BRAND"] == sim_brand]

        if not sim_df.empty:
            # ─── COMPUTE SIMULATION ───
            if preset == "match":
                # Match competitor price
                sim_df["NEW_PRICE"] = sim_df.apply(
                    lambda r: round(r["PRIMARY_COMPETITOR_PRICE"], 2) if pd.notna(r["PRIMARY_COMPETITOR_PRICE"]) else r["OUR_CURRENT_PRICE"], axis=1)
            elif preset == "undercut":
                sim_df["NEW_PRICE"] = sim_df.apply(
                    lambda r: round(r["PRIMARY_COMPETITOR_PRICE"] * 0.95, 2) if pd.notna(r["PRIMARY_COMPETITOR_PRICE"]) else round(r["OUR_CURRENT_PRICE"] * 0.95, 2), axis=1)
            else:
                sim_df["NEW_PRICE"] = (sim_df["OUR_CURRENT_PRICE"] * (1 + price_change / 100)).round(2)

            sim_df["NEW_MARGIN_USD"] = (sim_df["NEW_PRICE"] - sim_df["OUR_COST_PRICE"]).round(2)
            sim_df["NEW_MARGIN_PCT"] = ((sim_df["NEW_MARGIN_USD"] / sim_df["NEW_PRICE"]) * 100).round(1)
            sim_df["NEW_GAP_PCT"] = sim_df.apply(
                lambda r: round((r["NEW_PRICE"] - r["PRIMARY_COMPETITOR_PRICE"]) / r["PRIMARY_COMPETITOR_PRICE"] * 100, 1)
                if pd.notna(r["PRIMARY_COMPETITOR_PRICE"]) and r["PRIMARY_COMPETITOR_PRICE"] > 0 else None, axis=1)
            sim_df["NEW_POSITION"] = sim_df["NEW_GAP_PCT"].apply(
                lambda g: "OVERPRICED" if pd.notna(g) and g > 5 else ("UNDERPRICED" if pd.notna(g) and g < -5 else "PARITY"))

            # Aggregate metrics
            current_total_margin = sim_df["OUR_MARGIN_AMOUNT_USD"].sum()
            new_total_margin = sim_df["NEW_MARGIN_USD"].sum()
            margin_impact = new_total_margin - current_total_margin
            skus_affected = len(sim_df)

            # Position changes
            position_improved = len(sim_df[(sim_df["OVERALL_COMPETITIVE_POSITIONING_STATUS"] == "OVERPRICED") & (sim_df["NEW_POSITION"] != "OVERPRICED")])
            position_worsened = len(sim_df[(sim_df["OVERALL_COMPETITIVE_POSITIONING_STATUS"] != "OVERPRICED") & (sim_df["NEW_POSITION"] == "OVERPRICED")])

            # Risk assessment
            negative_margin_skus = len(sim_df[sim_df["NEW_MARGIN_PCT"] < 0])
            extreme_gap_skus = len(sim_df[(sim_df["NEW_GAP_PCT"].notna()) & (sim_df["NEW_GAP_PCT"].abs() > 20)])
            sim_df["RISK_FLAG"] = sim_df.apply(
                lambda r: "🔴 NEGATIVE MARGIN" if r["NEW_MARGIN_PCT"] < 0 else ("🟡 HIGH GAP" if pd.notna(r["NEW_GAP_PCT"]) and abs(r["NEW_GAP_PCT"]) > 20 else "🟢 OK"), axis=1)

            # ─── AI INSIGHT BANNER (3 cards) ───
            impact_color = "#4ade80" if margin_impact >= 0 else "#fbbf24"
            direction = "increase" if price_change > 0 else "decrease" if price_change < 0 else "match"

            risk_level = "LOW"
            risk_color = "#4ade80"
            risk_text = "No SKUs at risk — safe to proceed"
            if negative_margin_skus > 0:
                risk_level = "HIGH"
                risk_color = "#fbbf24"
                risk_text = f"{negative_margin_skus} SKUs would have negative margins — do NOT proceed"
            elif extreme_gap_skus > 3:
                risk_level = "MEDIUM"
                risk_color = "#fbbf24"
                risk_text = f"{extreme_gap_skus} SKUs with extreme competitive gap (>20%) — review before applying"

            st.markdown(f"""
            <div style="background:linear-gradient(135deg, #0f2027 0%, #1a2332 50%, #0d1b2a 100%);
                        border:1px solid #01b8fb; border-radius:10px; padding:14px 18px; margin-bottom:10px;">
                <div style="display:flex; align-items:center; margin-bottom:6px;">
                    <span style="font-size:1rem; margin-right:8px;">🧠</span>
                    <span style="font-size:0.8rem; font-weight:700; color:#01b8fb; text-transform:uppercase; letter-spacing:0.05em;">
                        AI Price Simulation — {skus_affected} SKUs
                    </span>
                </div>
                <p style="color:#ecf6fd; font-size:0.84rem; line-height:1.5; margin:0 0 8px 0;">
                    Simulating price {direction} across <b>{skus_affected}</b> SKUs.
                    {'Using preset: <b>' + preset.upper() + '</b>' if preset not in ['reset', 'margin'] else f'Applying <b>{price_change}%</b> adjustment'}.
                    Projected portfolio margin: <span style="color:{impact_color};font-weight:600;">${new_total_margin:,.0f}</span>
                    ({'+' if margin_impact >= 0 else ''}{margin_impact:,.0f}).
                </p>
                <div style="display:flex;gap:16px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:180px;background:{'#0d2818' if margin_impact >= 0 else '#1c1007'};border:1px solid {'#166534' if margin_impact >= 0 else '#92400e'};border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:{impact_color};font-weight:700;margin:0;text-transform:uppercase;">💰 Margin Impact</p>
                        <p style="font-size:1.1rem;color:#ecf6fd;margin:2px 0;font-weight:700;">{'+' if margin_impact >= 0 else ''}${margin_impact:,.0f}</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">From ${current_total_margin:,.0f} → ${new_total_margin:,.0f}</p>
                    </div>
                    <div style="flex:1;min-width:180px;background:#030c25;border:1px solid #1e40af;border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:#60a5fa;font-weight:700;margin:0;text-transform:uppercase;">🎯 Competitive Shift</p>
                        <p style="font-size:0.78rem;color:#ecf6fd;margin:2px 0;font-weight:600;">{position_improved} improved · {position_worsened} worsened</p>
                        <p style="font-size:0.7rem;color:#8ec9f5;margin:0;">SKUs moving from overpriced to parity or better</p>
                    </div>
                    <div style="flex:1;min-width:180px;background:{'#1c1007' if risk_level == 'HIGH' else '#030c25'};border:1px solid {'#92400e' if risk_level == 'HIGH' else '#1e40af'};border-radius:6px;padding:8px 12px;">
                        <p style="font-size:0.68rem;color:{risk_color};font-weight:700;margin:0;text-transform:uppercase;">⚠ Risk: {risk_level}</p>
                        <p style="font-size:0.72rem;color:#ecf6fd;margin:2px 0;line-height:1.4;">{risk_text}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ─── KPI ROW ───
            kpi_cols = st.columns(4)
            with kpi_cols[0]:
                render_kpi("CURRENT MARGIN", f"${current_total_margin:,.0f}", f"{skus_affected} SKUs", "up")
            with kpi_cols[1]:
                render_kpi("SIMULATED MARGIN", f"${new_total_margin:,.0f}", f"After simulation", "up" if new_total_margin >= current_total_margin else "down")
            with kpi_cols[2]:
                render_kpi("MARGIN IMPACT", f"{'+'if margin_impact>=0 else ''}${margin_impact:,.0f}", "Projected change", "up" if margin_impact >= 0 else "down")
            with kpi_cols[3]:
                render_kpi("AT RISK SKUs", f"{negative_margin_skus + extreme_gap_skus}", f"{negative_margin_skus} negative margin, {extreme_gap_skus} extreme gap", "down" if negative_margin_skus > 0 else "up")

            st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

            # ─── BEFORE vs AFTER CHART + AT RISK CALLOUT (side by side) ───
            col_chart, col_risk = st.columns([6, 4])

            with col_chart:
                st.markdown("**Margin Distribution — Before vs After**")
                margin_compare = pd.DataFrame({
                    "Current Margin %": sim_df["OUR_MARGIN_PERCENTAGE"].values,
                    "Simulated Margin %": sim_df["NEW_MARGIN_PCT"].values
                }, index=sim_df["PRODUCT_NAME"].values)
                st.bar_chart(margin_compare, height=250)

            with col_risk:
                st.markdown("**At Risk SKUs** — _Items flagged by simulation_")
                at_risk_df = sim_df[sim_df["RISK_FLAG"] != "🟢 OK"]
                if not at_risk_df.empty:
                    for _, row in at_risk_df.head(5).iterrows():
                        flag_color = "#fbbf24" if "NEGATIVE" in row["RISK_FLAG"] else "#fbbf24"
                        st.markdown(f"""
                        <div style="background:#0a1a3a;border-left:3px solid {flag_color};border-radius:0 6px 6px 0;padding:6px 10px;margin:4px 0;">
                            <p style="font-size:0.72rem;font-weight:700;color:#ecf6fd;margin:0;">{row['PRODUCT_NAME'][:30]}</p>
                            <p style="font-size:0.65rem;color:#8ec9f5;margin:1px 0;">${row['OUR_CURRENT_PRICE']} → ${row['NEW_PRICE']} · Margin: {row['NEW_MARGIN_PCT']}%</p>
                            <p style="font-size:0.65rem;color:{flag_color};margin:0;">{row['RISK_FLAG']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown('<p style="font-size:0.78rem;color:#4ade80;">All SKUs within safe parameters.</p>', unsafe_allow_html=True)

            st.markdown('<hr style="margin:8px 0;border:none;border-top:1px solid #1a3a5c;">', unsafe_allow_html=True)

            # ─── SIMULATION DETAIL TABLE ───
            st.markdown("**SKU-Level Impact** — _Current vs simulated pricing_")
            display_sim = sim_df[["PRODUCT_NAME", "OUR_CURRENT_PRICE", "NEW_PRICE",
                                   "OUR_MARGIN_PERCENTAGE", "NEW_MARGIN_PCT",
                                   "NEW_POSITION", "RISK_FLAG"]].rename(columns={
                "PRODUCT_NAME": "Product",
                "OUR_CURRENT_PRICE": "Current ($)",
                "NEW_PRICE": "Simulated ($)",
                "OUR_MARGIN_PERCENTAGE": "Current Margin %",
                "NEW_MARGIN_PCT": "New Margin %",
                "NEW_POSITION": "New Position",
                "RISK_FLAG": "Risk"
            })
            render_table(display_sim.reset_index(drop=True))
        else:
            st.info("No SKUs match the selected filters.")
    else:
        st.info("No pricing data available for simulation.")
