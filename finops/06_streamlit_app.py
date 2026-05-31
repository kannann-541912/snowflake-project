# streamlit_runtime: warehouse
import streamlit as st
import pandas as pd
import plotly.express as px
import _snowflake
import json
import base64
from snowflake.snowpark.context import get_active_session
from styles import (
    apply_theme,
    app_header,
    metric_card,
    PLOTLY_LAYOUT,
    CHART_COLORS
)

session = get_active_session()
session.use_warehouse('AGENT_DEMO_WH')

apply_theme()

try:
    logo = session.file.get_stream(
        "@DEMO_DEV.PUBLIC.SHARED_ASSETS/"
        "_shared_theme/Mastech Digital-White 4.svg",
        decompress=False,
    ).read()
    logo_loaded = True
except Exception:
    logo_loaded = False

header_logo, header_text = st.columns([1, 5])

with header_logo:
    if logo_loaded:
        b64 = base64.b64encode(logo).decode()
        st.markdown(
            f'<img src="data:image/svg+xml;base64,{b64}" width="160"/>',
            unsafe_allow_html=True
        )

with header_text:
    app_header(
        "\U0001f4a1 FinOps Value Intelligence",
        "Compute Investment v/s Business Outcome"
        " \u2014 Fraud Intelligence"
    )

st.divider()

@st.cache_data(ttl=3600)
def get_kpi_data():
    session = get_active_session()
    try:
        return session.sql("""
            SELECT
              ROUND(SUM(TOTAL_CREDITS),2) AS TOTAL_CREDITS_MTD,
              ROUND(SUM(IDLE_CREDITS)/NULLIF(SUM(TOTAL_CREDITS),0)*100,1) AS IDLE_PCT,
              ROUND(SUM(FRAUD_AMOUNT_PROTECTED)/NULLIF(SUM(TOTAL_CREDITS),0),2) AS VALUE_PER_CREDIT,
              ROUND(SUM(TOTAL_CREDITS)*3/NULLIF(SUM(ALERTS_PROCESSED),0),4) AS COST_PER_ALERT
            FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
            WHERE VALUE_DATE >= DATE_TRUNC('MONTH', CURRENT_DATE())
        """).to_pandas()
    except Exception as e:
        st.error(f"KPI load failed: {e}")
        return None


@st.cache_data(ttl=3600)
def get_chart_data():
    session = get_active_session()
    try:
        return session.sql("""
            SELECT VALUE_DATE,
                   PRODUCTIVE_CREDITS,
                   IDLE_CREDITS,
                   FRAUD_AMOUNT_PROTECTED
            FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
            WHERE VALUE_DATE >= DATEADD('DAY',-30,CURRENT_DATE())
            ORDER BY VALUE_DATE ASC
        """).to_pandas()
    except Exception as e:
        st.error(f"Chart load failed: {e}")
        return None


st.markdown("### \U0001f4ca Key Metrics")
kpi = get_kpi_data()
if kpi is None or kpi.empty:
    st.warning("No data for current month")
else:
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        metric_card(
            label="Credits MTD",
            value=f"{kpi['TOTAL_CREDITS_MTD'][0]:,}",
            icon="\U0001f50b"
        )
    with k2:
        metric_card(
            label="Idle %",
            value=f"{kpi['IDLE_PCT'][0]}%",
            icon="\U0001f4a4"
        )
    with k3:
        metric_card(
            label="Value / Credit",
            value=f"${kpi['VALUE_PER_CREDIT'][0]:,}",
            icon="\U0001f4b0"
        )
    with k4:
        metric_card(
            label="Cost / Alert",
            value=f"${kpi['COST_PER_ALERT'][0]}",
            icon="\U0001f4cb"
        )

st.divider()
st.markdown("### \U0001f4c8 Trends")
df = get_chart_data()
if df is not None and not df.empty:
    fig_a = px.bar(
        df,
        x='VALUE_DATE',
        y=['PRODUCTIVE_CREDITS', 'IDLE_CREDITS'],
        barmode='stack',
        color_discrete_map={
            'PRODUCTIVE_CREDITS': CHART_COLORS['productive'],
            'IDLE_CREDITS': CHART_COLORS['idle']
        },
        title='\u26a1 Productive vs Idle Credits (30 days)',
        labels={
            'VALUE_DATE': 'Date',
            'value': 'Credits',
            'variable': 'Type'
        },
        height=380
    )
    fig_a.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig_a, use_container_width=True)

    fig_b = px.line(
        df,
        x='VALUE_DATE',
        y='FRAUD_AMOUNT_PROTECTED',
        title='\U0001f6e1\ufe0f Fraud Amount Protected (30 days)',
        labels={
            'VALUE_DATE': 'Date',
            'FRAUD_AMOUNT_PROTECTED': '$ Amount'
        },
        height=380,
        color_discrete_sequence=[CHART_COLORS['line']]
    )
    fig_b.update_traces(line=dict(width=3))
    fig_b.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig_b, use_container_width=True)

st.divider()
st.markdown("### \U0001f916 Ask Your Data")
st.markdown(
    "<p style='color:#74b9ff;font-size:13px;'>"
    "Natural language queries over your cost "
    "and fraud intelligence data</p>",
    unsafe_allow_html=True
)

if "pending_question" not in st.session_state:
    st.session_state.pending_question = None
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None
if "last_question" not in st.session_state:
    st.session_state.last_question = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "prefill_text" not in st.session_state:
    st.session_state.prefill_text = ""

b1, b2, b3, spacer = st.columns([1, 1, 1, 2])
with b1:
    if st.button("\U0001f4b0 Value per credit"):
        st.session_state.prefill_text = (
            "What is my fraud amount protected "
            "per credit spent this month?"
        )
        st.rerun()
with b2:
    if st.button("\U0001f4cb SAR filing cost"):
        st.session_state.prefill_text = (
            "How many SARs were filed this month "
            "and what did each one cost in compute?"
        )
        st.rerun()
with b3:
    if st.button("\U0001f4a4 Worst idle days"):
        st.session_state.prefill_text = (
            "On my worst cost-efficiency days "
            "what happened?"
        )
        st.rerun()

input_col, send_col = st.columns([6, 1], gap="small")
with input_col:
    question = st.text_input(
        "",
        value=st.session_state.prefill_text,
        placeholder="Ask about your compute value...",
        label_visibility="collapsed"
    )
with send_col:
    send_clicked = st.button(
        "\u27a4",
        type="primary",
        use_container_width=True
    )

if send_clicked and question:
    st.session_state.pending_question = question
    st.session_state.prefill_text = ""
    st.rerun()

if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = None
    st.session_state.last_question = question
    st.session_state.last_result = None

    with st.spinner("\U0001f50d Analysing cost and value signals..."):
        try:
            response = _snowflake.send_snow_api_request(
                "POST",
                "/api/v2/cortex/analyst/message",
                {},
                {},
                {
                    "messages": [{
                        "role": "user",
                        "content": [{
                            "type": "text",
                            "text": question
                        }]
                    }],
                    "semantic_view": "ADMIN_DB.OPS.FINOPS_VALUE_INTELLIGENCE_SV"
                },
                {},
                30000
            )

            if int(response.get("status", 200)) >= 400:
                err_detail = ""
                try:
                    err_content = json.loads(response.get("content", "{}"))
                    err_detail = err_content.get("message", str(response.get("status")))
                except Exception:
                    err_detail = str(response.get("status"))
                st.session_state.last_answer = f"Analyst error: {err_detail}"
            else:
                content = json.loads(response["content"])
                items = content["message"]["content"]
                answer_parts = []
                for item in items:
                    if item["type"] == "text":
                        answer_parts.append(item["text"])
                    elif item["type"] == "sql":
                        try:
                            result = session.sql(item["statement"]).to_pandas()
                            st.session_state.last_result = result
                        except Exception as e:
                            answer_parts.append(f"Query error: {e}")
                st.session_state.last_answer = "\n\n".join(answer_parts)

        except Exception as e:
            st.session_state.last_answer = f"Request failed: {e}"

if st.session_state.last_question:
    with st.chat_message("user"):
        st.markdown(st.session_state.last_question)
if st.session_state.last_answer:
    with st.chat_message("assistant"):
        st.markdown(st.session_state.last_answer)
        if st.session_state.last_result is not None:
            st.dataframe(
                st.session_state.last_result,
                use_container_width=True
            )
