"""Fraud Intelligence Solution — AI-powered Alert investigation and SAR drafting.

Powered by Snowflake Cortex Agents. Provides real-time fraud triage,
ML-based scoring, and FinCEN-compliant SAR narrative generation.

Runtime: Snowflake warehouse runtime. Calls Cortex Agents via
SNOWFLAKE.CORTEX.DATA_AGENT_RUN SQL function (no REST API / EAI needed).
"""

import streamlit as st
import json, time, base64, html
from snowflake.snowpark.context import get_active_session
from styles import apply_theme, app_header, section_card, status_banner, badge, metric_card, info_card

TRIAGE_AGENT_DB = "DEMO_DEV"
TRIAGE_AGENT_SCHEMA = "FRAUD_INTELLIGENCE"
TRIAGE_AGENT_NAME = "FRAUD_TRIAGE_AGENT"

SAR_AGENT_DB = "DEMO_DEV"
SAR_AGENT_SCHEMA = "FRAUD_INTELLIGENCE"
SAR_AGENT_NAME = "FRAUD_SAR_AGENT"


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _rerun():
    if hasattr(st, "rerun"):
        _rerun()
    else:
        st.experimental_rerun()





def _tool_description(name: str) -> str:
    descriptions = {
        "lookup_customer_profile": "Fetching customer profile data",
        "get_transaction_history": "Retrieving transaction history",
        "check_fraud_model_score": "Running ML fraud scoring model",
        "search_alerts": "Searching alert records",
        "get_account_activity": "Checking account activity patterns",
        "query_watchlists": "Screening against watchlists",
        "get_kyc_status": "Checking KYC verification status",
        "generate_sar_narrative": "Drafting SAR narrative",
    }
    for key, desc in descriptions.items():
        if key in name.lower():
            return desc
    return ""


def _render_tool_card(t: dict) -> str:
    s = t.get("status", "running")
    icon = "\u2705" if s == "completed" else ("\u274c" if s in ("failed", "incomplete") else "\u23f3")
    name = t.get("name", "unknown").strip()
    desc = _tool_description(name)
    line = f"{icon} **{name}**"
    if desc:
        line += f"  \n{desc}"
    return line


def _render_tool_chain(tool_execs: list, elapsed_sec: float = 0.0) -> str:
    if not tool_execs:
        return "_No tools executed yet._"
    cards = [f"{i}. {_render_tool_card(t)}" for i, t in enumerate(tool_execs, 1)]
    elapsed_str = f"{elapsed_sec:.1f}s" if elapsed_sec > 0 else "N/A"
    cards.append(f"\nTotal tools: {len(tool_execs)} | Agent response time: {elapsed_str}")
    return "\n\n".join(cards)


def _call_agent(agent_name: str, messages: list, db: str = TRIAGE_AGENT_DB, schema: str = TRIAGE_AGENT_SCHEMA):
    session = get_active_session()
    fqn = f"{db}.{schema}.{agent_name}"
    body = json.dumps({"messages": messages})
    result = session.sql(
        "SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN(?, ?)) AS RESP",
        params=[fqn, body],
    ).collect()
    if not result or result[0]["RESP"] is None:
        raise RuntimeError(f"Agent '{agent_name}' returned empty response")
    resp = result[0]["RESP"]
    return json.loads(resp) if isinstance(resp, str) else resp


def _parse_agent_response(resp_data: dict):
    full_text = ""
    tool_chain = []

    if not isinstance(resp_data, dict):
        return None, tool_chain

    content_items = resp_data.get("content", [])

    if isinstance(content_items, list):
        for item in content_items:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type", "")

            if item_type == "text":
                text_val = item.get("text", "")
                if text_val:
                    full_text += text_val + "\n"

            elif item_type == "tool_result":
                tr = item.get("tool_result", item)
                entry = {
                    "name": tr.get("name", "unknown").strip(),
                    "status": "completed" if tr.get("status") not in ("error", "failed") else "failed",
                    "duration_ms": tr.get("duration_ms", 0),
                    "output": str(tr.get("content", ""))[:1000],
                }
                tool_chain.append(entry)

    if not full_text:
        choices = resp_data.get("choices", [])
        if choices:
            message = choices[0].get("message", choices[0].get("delta", {}))
            full_text = message.get("content", "") or ""
        if not full_text:
            full_text = resp_data.get("text", resp_data.get("message", "")) or ""

    return full_text.replace("\ufffd", "").strip() or None, tool_chain


def call_triage_agent(alert_id: str, customer_id: str, session=None):
    live_scoring = False
    if session is not None:
        try:
            has_score = session.sql(
                f"SELECT ML_FRAUD_SCORE FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED WHERE ALERT_ID = '{alert_id}' LIMIT 1"
            ).collect()
            if not has_score or has_score[0]["ML_FRAUD_SCORE"] is None:
                live_scoring = True
        except Exception:
            pass

    prompt = f"Investigate alert {alert_id} for customer {customer_id} and produce a full investigation dossier."
    if live_scoring:
        prompt += " This alert has no pre-computed ML score. Use FraudScorerLive for real-time model inference."

    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
    t0 = time.time()
    resp_data = _call_agent(TRIAGE_AGENT_NAME, messages, TRIAGE_AGENT_DB, TRIAGE_AGENT_SCHEMA)
    elapsed = time.time() - t0
    text, tool_chain = _parse_agent_response(resp_data)
    return text, tool_chain, elapsed


def call_sar_agent(alert_id: str, customer_id: str, rule_code: str):
    messages = [{
        "role": "user",
        "content": [{
            "type": "text",
            "text": (
                f"Draft a FinCEN-compliant SAR narrative for alert {alert_id}, "
                f"customer {customer_id}. Rule: {rule_code}. "
                "Cover who/what/when/where/why. Include CITATION BLOCK."
            ),
        }],
    }]
    t0 = time.time()
    resp_data = _call_agent(SAR_AGENT_NAME, messages, SAR_AGENT_DB, SAR_AGENT_SCHEMA)
    elapsed = time.time() - t0
    text, tool_chain = _parse_agent_response(resp_data)
    return text, tool_chain, elapsed


@st.cache_data(ttl=300, show_spinner="Loading alerts...")
def load_alerts(_session):
    return _session.sql(
        """
        SELECT DISTINCT ALERT_ID, CUSTOMER_ID, ALERT_DATE, ALERT_RISK_SCORE AS RISK_SCORE,
               ALERT_STATUS, RULE_CODE, FULL_NAME, TENURE_RISK_TIER
        FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHMENT_WITH_SCORING
        WHERE ALERT_STATUS NOT IN ('CLOSED_CONFIRMED', 'CLOSED_FP')
        ORDER BY ALERT_RISK_SCORE DESC
        LIMIT 200
        """
    ).to_pandas()


@st.cache_data(ttl=120, show_spinner=False)
def load_customer_profile(_session, _customer_id):
    return _session.sql(
        "SELECT * FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_CUSTOMER_PROFILE WHERE CUSTOMER_ID = ?",
        params=[_customer_id],
    ).to_pandas()


@st.cache_data(ttl=120, show_spinner=False)
def load_velocity(_session, _customer_id):
    return _session.sql(
        "SELECT * FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_VELOCITY_COUNTERS WHERE CUSTOMER_ID = ?",
        params=[_customer_id],
    ).to_pandas()


def _write_analyst_decision(session, alert_id, customer_id, decision, sar_filed,
                            sar_recommended, tool_chain, investigation_result, rule_code):
    ml_score = None
    agent_recommendation = None
    agent_confidence = None
    agent_reasoning = None
    rule_ml_agreement = None

    for tool in (tool_chain or []):
        if "FraudScorer" in tool.get("name", "") or "SCORE" in tool.get("name", "").upper():
            try:
                output = json.loads(tool.get("output", "{}"))
                ml_score = output.get("fraud_probability")
            except Exception:
                pass

    if investigation_result:
        lines = investigation_result.upper()
        if "ESCALATE_TO_SAR" in lines:
            agent_recommendation = "ESCALATE_TO_SAR"
        elif "CLOSE_FALSE_POSITIVE" in lines:
            agent_recommendation = "FALSE_POSITIVE"
        elif "CONTINUE_MONITORING" in lines:
            agent_recommendation = "CONTINUE_MONITORING"
        else:
            agent_recommendation = "REQUEST_MORE_INFO"
        if "CONFIDENCE_SCORE:" in lines:
            try:
                conf_str = investigation_result.split("CONFIDENCE_SCORE:")[1].strip().split()[0]
                conf_val = float(conf_str)
                if conf_val >= 0.75:
                    agent_confidence = "HIGH"
                elif conf_val >= 0.5:
                    agent_confidence = "MEDIUM"
                else:
                    agent_confidence = "LOW"
            except Exception:
                agent_confidence = "MEDIUM"
        agent_reasoning = (investigation_result or "")[:2000]

    if ml_score is not None and agent_recommendation:
        is_fraud_agent = agent_recommendation in ("ESCALATE_TO_SAR",)
        is_fraud_ml = (ml_score or 0) >= 0.5
        rule_ml_agreement = is_fraud_agent == is_fraud_ml

    import uuid
    from datetime import datetime, timezone
    decision_id = "DEC_" + str(uuid.uuid4()).replace("-", "")[:16].upper()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    ml_score_param = None
    if ml_score is not None and str(ml_score).lower() != "none":
        try:
            ml_score_param = float(ml_score)
        except (TypeError, ValueError):
            ml_score_param = None

    ml_score_sql = "NULL" if ml_score_param is None else str(ml_score_param)

    try:
        session.sql(
            "INSERT INTO DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_ANALYST_DECISIONS "
            "(DECISION_ID, ALERT_ID, CUSTOMER_ID, ANALYST_ID, DECISION, "
            " SAR_RECOMMENDED, SAR_FILED, ML_SCORE_AT_DECISION, AGENT_RECOMMENDATION, "
            " AGENT_CONFIDENCE, AGENT_REASONING_SUMMARY, RULE_TRIGGERED, RULE_ML_AGREEMENT, "
            " SAR_THRESHOLD_MET, DECISION_TIMESTAMP, SOURCE_SYSTEM, INGESTED_AT) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?, {ml_score_sql}, ?, ?, ?, ?, ?, ?, ?, 'AGENT_ASSISTED_TRIAGE', ?)",
            params=[
                decision_id, alert_id, customer_id, "ANALYST_APP", decision,
                sar_recommended, sar_filed, agent_recommendation,
                agent_confidence, agent_reasoning, rule_code, rule_ml_agreement,
                sar_filed, now, now,
            ],
        ).collect()
        return True, decision_id
    except Exception as e:
        return False, str(e)


@st.cache_data(ttl=300, show_spinner=False)
def _load_governance_data(_session):
    perf = _session.sql(
        "SELECT EVAL_DATE, MODEL_VERSION, PRECISION_SCORE, RECALL_SCORE, F1_SCORE, AUC_ROC "
        "FROM DEMO_DEV.FRAUD_INTELLIGENCE.SLV_MODEL_PERFORMANCE_LOG ORDER BY EVAL_DATE"
    ).to_pandas()
    label_dist = _session.sql(
        "SELECT CLASS_LABEL, COUNT(*) AS CNT FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ML_TRAINING_SET "
        "GROUP BY CLASS_LABEL"
    ).to_pandas()
    decisions = _session.sql(
        "SELECT d.DECISION_ID, d.ALERT_ID, d.CUSTOMER_ID, d.ANALYST_ID, d.DECISION, "
        "d.SAR_FILED, d.ML_SCORE_AT_DECISION, d.AGENT_RECOMMENDATION, d.AGENT_CONFIDENCE, "
        "d.AGENT_REASONING_SUMMARY, d.RULE_TRIGGERED, d.RULE_ML_AGREEMENT, "
        "d.SAR_THRESHOLD_MET, d.DECISION_TIMESTAMP "
        "FROM DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_ANALYST_DECISIONS d "
        "ORDER BY d.DECISION_TIMESTAMP DESC LIMIT 500"
    ).to_pandas()
    rule_alignment = _session.sql(
        "SELECT RULE_TRIGGERED, "
        "  COUNT(*) AS TOTAL_DECISIONS, "
        "  SUM(CASE WHEN RULE_ML_AGREEMENT = TRUE THEN 1 ELSE 0 END) AS AGREED, "
        "  ROUND(AVG(CASE WHEN RULE_ML_AGREEMENT = TRUE THEN 1.0 ELSE 0.0 END) * 100, 1) AS AGREEMENT_PCT "
        "FROM DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_ANALYST_DECISIONS "
        "WHERE RULE_TRIGGERED IS NOT NULL "
        "GROUP BY RULE_TRIGGERED ORDER BY AGREEMENT_PCT"
    ).to_pandas()
    sar_pipeline = _session.sql(
        "SELECT "
        "  COUNT(*) AS TOTAL_ALERTS_REVIEWED, "
        "  SUM(CASE WHEN SAR_RECOMMENDED = TRUE THEN 1 ELSE 0 END) AS SAR_RECOMMENDED_CNT, "
        "  SUM(CASE WHEN SAR_FILED = TRUE THEN 1 ELSE 0 END) AS SAR_FILED_CNT "
        "FROM DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_ANALYST_DECISIONS"
    ).to_pandas()
    model_meta = _session.sql(
        "SELECT MODEL_NAME, MODEL_VERSION, MODEL_STATUS, LAST_TRAINED_AT "
        "FROM DEMO_DEV.FRAUD_INTELLIGENCE.SLV_FRAUD_MODEL_METADATA"
    ).to_pandas()
    return perf, label_dist, decisions, rule_alignment, sar_pipeline, model_meta


def render_governance_tab(session):
    st.markdown("### Model & Decision Governance")
    perf, label_dist, decisions, rule_alignment, sar_pipeline, model_meta = _load_governance_data(session)

    meta_row = model_meta.iloc[0].to_dict() if not model_meta.empty else {}
    total_reviewed = safe_int(sar_pipeline["TOTAL_ALERTS_REVIEWED"].iloc[0]) if not sar_pipeline.empty else 0
    sar_filed = safe_int(sar_pipeline["SAR_FILED_CNT"].iloc[0]) if not sar_pipeline.empty else 0
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Active model", meta_row.get("MODEL_VERSION", "N/A"), icon="model_training")
    with m2:
        metric_card("Model status", meta_row.get("MODEL_STATUS", "N/A"), icon="check_circle")
    with m3:
        metric_card("Alerts reviewed", str(total_reviewed), icon="fact_check")
    with m4:
        metric_card("SARs filed", str(sar_filed), icon="description")

    st.divider()
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("**Model Performance Over Time**")
        if len(perf) >= 2:
            chart_df = perf.set_index("EVAL_DATE")[["F1_SCORE", "AUC_ROC", "PRECISION_SCORE", "RECALL_SCORE"]]
            st.line_chart(chart_df, color=["#01b8fb", "#9f7aea", "#48bb78", "#f6ad55"])
        elif len(perf) == 1:
            st.info("Need 2+ model evaluations to display trend. Current metrics shown below.")
            row = perf.iloc[0]
            st.markdown(
                f"- **F1:** {row['F1_SCORE']:.3f} &nbsp; **AUC-ROC:** {row['AUC_ROC']:.3f} &nbsp; "
                f"**Precision:** {row['PRECISION_SCORE']:.3f} &nbsp; **Recall:** {row['RECALL_SCORE']:.3f}"
            )
        else:
            st.info("No performance logs yet.")

        st.markdown("**Training Label Distribution**")
        if not label_dist.empty:
            total_labels = label_dist["CNT"].sum()
            for _, row in label_dist.iterrows():
                pct = row["CNT"] / total_labels * 100
                color = "#e67e22" if row["CLASS_LABEL"] == "FRAUD" else "#48bb78"
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                    f'<span style="background:{color};width:12px;height:12px;border-radius:2px;display:inline-block"></span>'
                    f'<b>{row["CLASS_LABEL"]}</b>: {int(row["CNT"]):,} ({pct:.1f}%)</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No training data yet.")

    with col_right:
        st.markdown("**Rule vs ML Agreement by Rule Code**")
        if not rule_alignment.empty:
            for _, row in rule_alignment.iterrows():
                pct = float(row["AGREEMENT_PCT"] or 0)
                bar_color = "#48bb78" if pct >= 70 else ("#ed8936" if pct >= 40 else "#e67e22")
                st.markdown(
                    f'<div style="margin:4px 0"><b>{row["RULE_TRIGGERED"]}</b> '
                    f'<span style="color:#a0aec0">({int(row["TOTAL_DECISIONS"])} decisions)</span><br>'
                    f'<div style="background:#2d3748;border-radius:4px;height:8px;width:100%">'
                    f'<div style="background:{bar_color};border-radius:4px;height:8px;width:{min(pct,100):.0f}%"></div></div>'
                    f'<span style="font-size:0.8rem;color:{bar_color}">{pct:.1f}% agreement</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("No rule-ML agreement data yet. Decisions will appear here once analysts review alerts.")

        st.markdown("**SAR Filing Pipeline**")
        if not sar_pipeline.empty:
            rec = safe_int(sar_pipeline["SAR_RECOMMENDED_CNT"].iloc[0])
            filed = safe_int(sar_pipeline["SAR_FILED_CNT"].iloc[0])
            conversion = (filed / rec * 100) if rec > 0 else 0
            st.markdown(
                f"- SAR recommended by agent: **{rec}**\n"
                f"- SAR filed by analyst: **{filed}**\n"
                f"- Conversion rate: **{conversion:.1f}%**"
            )

    st.divider()
    st.markdown("**Analyst Decision Audit Log**")
    if not decisions.empty:
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            decision_filter = st.multiselect(
                "Filter by decision",
                options=decisions["DECISION"].dropna().unique().tolist(),
                default=[],
            )
        with filter_col2:
            analyst_filter = st.multiselect(
                "Filter by analyst",
                options=decisions["ANALYST_ID"].dropna().unique().tolist(),
                default=[],
            )
        filtered = decisions.copy()
        if decision_filter:
            filtered = filtered[filtered["DECISION"].isin(decision_filter)]
        if analyst_filter:
            filtered = filtered[filtered["ANALYST_ID"].isin(analyst_filter)]
        display_cols = [
            "ALERT_ID", "CUSTOMER_ID", "ANALYST_ID", "DECISION",
            "ML_SCORE_AT_DECISION", "AGENT_RECOMMENDATION", "AGENT_CONFIDENCE",
            "RULE_TRIGGERED", "RULE_ML_AGREEMENT", "SAR_FILED", "SAR_THRESHOLD_MET",
            "DECISION_TIMESTAMP",
        ]
        st.dataframe(
            filtered[[c for c in display_cols if c in filtered.columns]],
            use_container_width=True,
            height=300,
        )

    else:
        st.info("No analyst decisions recorded yet. Decisions are written here when analysts confirm or reject alerts.")

    st.divider()
    st.markdown("### A/B Model Testing")
    try:
        ab_data = session.sql(
            "SELECT "
            "  RESOURCE_ATTRIBUTES:\"snow.model.version.name\"::VARCHAR AS MODEL_VERSION, "
            "  COUNT(*) AS REQUEST_COUNT, "
            "  AVG(RECORD_ATTRIBUTES:\"snow.model_serving.response.data.output_feature_1\"::FLOAT) AS AVG_FRAUD_PROB "
            "FROM TABLE(INFERENCE_TABLE('FRAUD_DETECTION_MODEL')) "
            "WHERE TIMESTAMP > DATEADD(HOUR, -24, CURRENT_TIMESTAMP()) "
            "GROUP BY MODEL_VERSION ORDER BY MODEL_VERSION"
        ).to_pandas()

        if not ab_data.empty:
            total_reqs = ab_data["REQUEST_COUNT"].sum()
            ab_col1, ab_col2 = st.columns(2)
            with ab_col1:
                st.markdown("**Traffic Distribution (Last 24h)**")
                for _, row in ab_data.iterrows():
                    pct = row["REQUEST_COUNT"] / total_reqs * 100
                    color = "#4299e1" if "V1" in str(row["MODEL_VERSION"]) else "#9f7aea"
                    st.markdown(
                        f'<div style="margin:6px 0"><b>{row["MODEL_VERSION"]}</b> '
                        f'<span style="color:#a0aec0">({int(row["REQUEST_COUNT"])} reqs, {pct:.0f}%)</span><br>'
                        f'<div style="background:#2d3748;border-radius:4px;height:10px;width:100%">'
                        f'<div style="background:{color};border-radius:4px;height:10px;width:{min(pct,100):.0f}%"></div></div></div>',
                        unsafe_allow_html=True,
                    )
            with ab_col2:
                st.markdown("**Avg Fraud Probability by Version**")
                for _, row in ab_data.iterrows():
                    avg_prob = safe_float(row.get("AVG_FRAUD_PROB", 0))
                    st.metric(str(row["MODEL_VERSION"]), f"{avg_prob:.4f}")

            st.markdown("**Raw Inference Log (Last 10)**")
            recent_logs = session.sql(
                "SELECT TIMESTAMP, "
                "  RESOURCE_ATTRIBUTES:\"snow.model.version.name\"::VARCHAR AS VERSION, "
                "  RECORD_ATTRIBUTES:\"snow.model_serving.response.code\"::INT AS STATUS_CODE, "
                "  RECORD_ATTRIBUTES:\"snow.model_serving.response.data.output_feature_1\"::FLOAT AS FRAUD_PROB "
                "FROM TABLE(INFERENCE_TABLE('FRAUD_DETECTION_MODEL')) "
                "ORDER BY TIMESTAMP DESC LIMIT 10"
            ).to_pandas()
            if not recent_logs.empty:
                st.dataframe(recent_logs, use_container_width=True, height=200)
        else:
            st.info("No A/B inference data available. Model services must be deployed and receiving traffic to populate comparison metrics.")
    except Exception as e:
        st.info(f"A/B testing requires model services. Deploy via the validation notebook (`validate_ab_testing.ipynb`) to enable inference logging. ({type(e).__name__})")


def init_session_state():
    defaults = {
        "investigation_result": None,
        "investigation_tool_chain": None,
        "investigation_elapsed": 0.0,
        "investigated_alert_id": None,
        "sar_alert_context": None,
        "sar_draft": None,
        "sar_tool_chain": None,
        "sar_elapsed": 0.0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def render_alert_selector(alerts_df, alert_ids):
    col_dd, col_meta, col_btn = st.columns([2, 4, 1])

    with col_dd:
        selected_idx = st.selectbox(
            "Alert ID",
            range(len(alert_ids)),
            format_func=lambda i: alert_ids[i],
            key="alert_selector",
        )

    alert_row = alerts_df.iloc[selected_idx]
    selected_alert_id = str(alert_row["ALERT_ID"])
    customer_id = str(alert_row["CUSTOMER_ID"])

    status = str(alert_row.get("ALERT_STATUS", ""))
    alert_date = alert_row.get("ALERT_DATE", "N/A")
    if hasattr(alert_date, "strftime"):
        alert_date = alert_date.strftime("%Y-%m-%d %H:%M")

    with col_meta:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding-top:28px">'
            f'<span style="font-weight:600">{html.escape(str(alert_row.get("FULL_NAME", "Unknown")))}</span>'
            f'<span style="color:#a0aec0">|</span>'
            f'<span style="color:#8ec9f5">{html.escape(str(alert_date))}</span>'
            f'<span style="color:#a0aec0">|</span>'
            f'<span style="color:#8ec9f5">Rule: {html.escape(str(alert_row.get("RULE_CODE", "N/A")))}</span>'
            f'<span style="color:#a0aec0">|</span>'
            f'{badge(html.escape(status), "orange" if status == "ESCALATED" else "teal")}'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_btn:
        st.markdown('<div style="padding-top:24px"></div>', unsafe_allow_html=True)
        if st.button("Investigate", type="primary", use_container_width=True):
            st.session_state.investigation_result = None
            st.session_state.investigation_tool_chain = None
            st.session_state.investigated_alert_id = selected_alert_id

    return alert_row, selected_alert_id, customer_id


def extract_ml_score_from_tool_chain(tool_chain):
    ml_score = None
    ml_risk_tier = None
    for tool in tool_chain:
        output = tool.get("output", "")
        if "fraud_probability" in output:
            try:
                json_start = output.find("{")
                json_end = output.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    score_data = json.loads(output[json_start:json_end])
                    ml_score = score_data.get("fraud_probability")
                    ml_risk_tier = score_data.get("risk_tier")
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
    return ml_score, ml_risk_tier


def render_investigation_results(selected_alert_id, risk_score, customer_id, alert_row):
    result = st.session_state.investigation_result

    if not result or st.session_state.investigated_alert_id != selected_alert_id:
        return

    st.markdown("---")

    tool_chain = st.session_state.investigation_tool_chain or []
    elapsed = st.session_state.get("investigation_elapsed", 0.0)
    ml_score, ml_risk_tier = extract_ml_score_from_tool_chain(tool_chain)

    if ml_score is not None:
        ml_score_f = safe_float(ml_score)
        ml_tier = ml_risk_tier or ("CRITICAL" if ml_score_f >= 0.8 else "HIGH" if ml_score_f >= 0.5 else "MEDIUM" if ml_score_f >= 0.3 else "LOW")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("ML Fraud Score", f"{ml_score_f:.4f}")
        mc2.metric("ML Risk Tier", ml_tier)
        mc3.metric("Rule Risk Score", f"{risk_score:.3f}")

    elapsed_str = f"{elapsed:.1f}s" if elapsed > 0 else ""
    with st.expander(f"Tool Execution - {len(tool_chain)} tools | {elapsed_str}", expanded=False):
        st.markdown(_render_tool_chain(tool_chain, elapsed))

    st.markdown(result)

    render_analyst_decision_buttons(selected_alert_id, customer_id, alert_row, risk_score)


def render_analyst_decision_buttons(selected_alert_id, customer_id, alert_row, risk_score):
    st.markdown("**Analyst decision**")
    dc1, dc2, dc3 = st.columns(3)
    with dc1:
        if st.button("Not fraud", use_container_width=True):
            st.session_state["_decision_msg"] = f"Alert {selected_alert_id} closed as FALSE POSITIVE."
    with dc2:
        if st.button("Needs review", use_container_width=True):
            st.session_state["_decision_msg"] = f"Alert {selected_alert_id} ESCALATED for review."
    with dc3:
        if st.button("File SAR", use_container_width=True, type="primary"):
            st.session_state.sar_alert_context = {
                "alert_id": selected_alert_id,
                "customer_id": customer_id,
                "rule_code": str(alert_row.get("RULE_CODE", "")),
                "full_name": str(alert_row.get("FULL_NAME", "")),
                "risk_score": risk_score,
            }
            st.session_state["_decision_msg"] = f"Alert {selected_alert_id} queued for SAR drafting. Switch to the **SAR Drafting** tab."

    if st.session_state.get("_decision_msg"):
        st.success(st.session_state["_decision_msg"])
        st.session_state["_decision_msg"] = None


def run_triage_agent(selected_alert_id, customer_id):
    if st.session_state.investigated_alert_id != selected_alert_id:
        return
    if st.session_state.investigation_result is not None:
        return

    try:
        with st.spinner("Agent investigating..."):
            dossier, tool_chain, elapsed = call_triage_agent(
                selected_alert_id, customer_id,
                session=get_active_session(),
            )
        st.session_state.investigation_result = dossier
        st.session_state.investigation_tool_chain = tool_chain
        st.session_state.investigation_elapsed = elapsed
        _rerun()
    except ConnectionError as e:
        st.error(f"Unable to reach triage agent. Please retry. ({e})")
        st.session_state.investigation_result = None
        st.session_state.investigated_alert_id = None
    except ValueError as e:
        st.error(f"Triage agent returned an unparseable response. ({e})")
        st.session_state.investigation_result = None
        st.session_state.investigated_alert_id = None
    except RuntimeError as e:
        st.error(f"Triage agent failed: {e}")
        st.session_state.investigation_result = None
        st.session_state.investigated_alert_id = None
    except Exception as e:
        st.error(f"Unexpected error during investigation: {type(e).__name__}: {e}")
        st.session_state.investigation_result = None
        st.session_state.investigated_alert_id = None


def render_investigation_tab(alert_row, selected_alert_id, customer_id, cp, vc):
    if st.session_state.investigated_alert_id and st.session_state.investigated_alert_id != selected_alert_id:
        st.session_state.investigation_result = None
        st.session_state.investigation_tool_chain = None
        st.session_state.investigated_alert_id = None

    risk_score = safe_float(alert_row.get("RISK_SCORE"))
    acct_age = safe_int(cp.get("MIN_ACCOUNT_AGE_DAYS"))
    prior_alerts = safe_int(cp.get("PRIOR_ALERT_COUNT"))
    txn_24h = safe_int(vc.get("TXN_COUNT_24H"))
    amt_24h = safe_float(vc.get("TXN_AMOUNT_24H"))
    tenure_tier = str(cp.get("TENURE_RISK_TIER", "N/A"))

    st.markdown(
        f'<span style="color:#8ec9f5;font-size:1.0rem">'
        f'Alert <code>{selected_alert_id}</code> \u2014 {html.escape(str(alert_row.get("FULL_NAME", "Unknown")))} '
        f'\u2014 {html.escape(str(alert_row.get("RULE_CODE", "N/A")))}</span>',
        unsafe_allow_html=True,
    )

    # ---- METRIC TILES ----------------------------------------------------
    # Visual: blue-accent metric_card() tiles (styles.py).
    # REVERT: replace this block with the original st.metric() calls below
    #         and remove the metric_card import.
    #     col1, col2, col3, col4 = st.columns(4)
    #     col1.metric("Risk score", f"{risk_score:.3f}")
    #     col2.metric("Account age", f"{acct_age}d")
    #     col3.metric("Prior alerts", prior_alerts)
    #     col4.metric("24h transactions", f"{txn_24h}  (${amt_24h:,.0f})")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Risk score", f"{risk_score:.3f}", icon="gpp_maybe", sub="rule-based")
    with col2:
        metric_card("Account age", f"{acct_age}d", icon="event_available", sub=tenure_tier)
    with col3:
        metric_card("Prior alerts", str(prior_alerts), icon="flag")
    with col4:
        metric_card("24h transactions", str(txn_24h), icon="payments", sub=f"${amt_24h:,.0f}")

    st.write("")

    left, right = st.columns(2)

    # ---- ALERT CONTEXT + CUSTOMER PROFILE -------------------------------
    # Visual: info_card() with tone-colored pills (styles.py).
    # REVERT: replace this with the original markdown blocks below and
    #         remove the info_card import.
    #     with left:
    #         st.markdown("**Alert context**")
    #         st.markdown(
    #             f"- **Rule:** {alert_row.get('RULE_CODE', 'N/A')}\n"
    #             f"- **Status:** {alert_row.get('ALERT_STATUS', 'N/A')}\n"
    #             f"- **Tenure risk:** {tenure_tier}\n"
    #             f"- **Alert history risk:** {cp.get('ALERT_HISTORY_RISK_TIER', 'N/A')}"
    #         )
    #     with right:
    #         st.markdown("**Customer profile**")
    #         st.markdown(
    #             f"- **Accounts:** {safe_int(cp.get('ACCOUNT_COUNT', 0))}\n"
    #             f"- **KYC complete:** {cp.get('KYC_COMPLETE', 'N/A')}\n"
    #             f"- **Synthetic ID flag:** {cp.get('IS_SYNTHETIC_FLAG', 'N/A')}\n"
    #             f"- **Distinct merchants 24h:** {safe_int(vc.get('DISTINCT_MERCHANTS_24H', 0))}"
    #         )

    def _tier_tone(tier_str):
        t = str(tier_str).upper()
        if t in ("HIGH", "CRITICAL"):
            return "critical"
        if t in ("MEDIUM", "MED"):
            return "warning"
        if t == "LOW":
            return "success"
        return "muted"

    def _bool_tone(val, *, true_is_good: bool):
        s = str(val).strip().lower()
        if s in ("true", "1", "yes"):
            return ("TRUE", "success" if true_is_good else "critical")
        if s in ("false", "0", "no"):
            return ("FALSE", "critical" if true_is_good else "success")
        return (str(val), "muted")

    rule_code = str(alert_row.get("RULE_CODE", "N/A"))
    status_val = str(alert_row.get("ALERT_STATUS", "N/A"))
    if status_val == "OPEN":
        status_tone = "warning"
    elif status_val == "ESCALATED":
        status_tone = "critical"
    elif status_val == "CLOSED":
        status_tone = "success"
    else:
        status_tone = "muted"
    hist_tier = str(cp.get("ALERT_HISTORY_RISK_TIER", "N/A"))

    kyc_value, kyc_tone = _bool_tone(cp.get("KYC_COMPLETE", "N/A"), true_is_good=True)
    syn_value, syn_tone = _bool_tone(cp.get("IS_SYNTHETIC_FLAG", "N/A"), true_is_good=False)

    with left:
        info_card(
            "Alert context",
            [
                ("gavel",     "Rule",               rule_code,  "neutral"),
                ("circle",    "Status",             status_val, status_tone),
                ("schedule",  "Tenure risk",        tenure_tier, _tier_tone(tenure_tier)),
                ("history",   "Alert history risk", hist_tier,  _tier_tone(hist_tier)),
            ],
            title_icon="shield",
        )

    with right:
        info_card(
            "Customer profile",
            [
                ("account_balance", "Accounts",           str(safe_int(cp.get("ACCOUNT_COUNT", 0))),                 ""),
                ("verified_user",   "KYC complete",       kyc_value,                                                  kyc_tone),
                ("report",          "Synthetic ID flag",  syn_value,                                                  syn_tone),
                ("storefront",      "Distinct merchants 24h", str(safe_int(vc.get("DISTINCT_MERCHANTS_24H", 0))),     ""),
            ],
            title_icon="person",
        )

    run_triage_agent(selected_alert_id, customer_id)
    render_investigation_results(selected_alert_id, risk_score, customer_id, alert_row)

    if st.session_state.investigated_alert_id is None:
        st.session_state.investigation_result = None
        st.session_state.investigation_tool_chain = None
        st.caption("Click **Investigate** above to run Cortex Agent analysis.")


def run_sar_agent(ctx):
    if st.button("Draft SAR narrative", type="primary", use_container_width=True):
        try:
            with st.spinner("Generating SAR narrative..."):
                draft, tool_chain, elapsed = call_sar_agent(
                    ctx["alert_id"], ctx["customer_id"], ctx["rule_code"],
                )
            st.session_state.sar_draft = draft
            st.session_state.sar_tool_chain = tool_chain
            st.session_state.sar_elapsed = elapsed
            _rerun()
        except ConnectionError as e:
            st.error(f"Unable to reach SAR agent. Please retry. ({e})")
        except ValueError as e:
            st.error(f"SAR agent returned an unparseable response. ({e})")
        except RuntimeError as e:
            st.error(f"SAR agent failed: {e}")
        except Exception as e:
            st.error(f"Unexpected error during SAR drafting: {type(e).__name__}: {e}")


def render_sar_draft(ctx):
    if not st.session_state.sar_draft:
        return

    tool_chain = st.session_state.sar_tool_chain or []
    elapsed = st.session_state.get("sar_elapsed", 0.0)
    elapsed_str = f"{elapsed:.1f}s" if elapsed > 0 else ""
    with st.expander(f"Tool Execution - {len(tool_chain)} tools | {elapsed_str}", expanded=False):
        st.markdown(_render_tool_chain(tool_chain, elapsed))

    st.markdown(st.session_state.sar_draft)

    st.markdown(
        '<div style="color:#a0aec0;font-size:0.78rem;margin-top:8px;">'
        "DRAFT_STATUS: REQUIRES_HUMAN_REVIEW &middot; SR11-7: TIER2 &middot; "
        "Agent cannot file SARs autonomously &middot; Analyst must review, edit and file"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("**Analyst action**")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        if st.button("Approve & file SAR", type="primary", use_container_width=True):
            st.session_state["_pending_sar_decision"] = {
                "alert_id": ctx["alert_id"],
                "customer_id": ctx["customer_id"],
                "decision": "CONFIRMED_FRAUD",
                "sar_filed": True,
                "sar_recommended": True,
                "tool_chain": st.session_state.sar_tool_chain,
                "investigation_result": st.session_state.investigation_result,
                "rule_code": ctx.get("rule_code", ""),
                "clear_draft": False,
            }
            _rerun()
    with sc2:
        if st.button("Request edits", use_container_width=True):
            st.session_state["_pending_sar_decision"] = {
                "alert_id": ctx["alert_id"],
                "customer_id": ctx["customer_id"],
                "decision": "NEEDS_REVIEW",
                "sar_filed": False,
                "sar_recommended": True,
                "tool_chain": st.session_state.sar_tool_chain,
                "investigation_result": st.session_state.investigation_result,
                "rule_code": ctx.get("rule_code", ""),
                "clear_draft": False,
            }
            _rerun()
    with sc3:
        if st.button("Reject draft", use_container_width=True):
            st.session_state["_pending_sar_decision"] = {
                "alert_id": ctx["alert_id"],
                "customer_id": ctx["customer_id"],
                "decision": "FALSE_POSITIVE",
                "sar_filed": False,
                "sar_recommended": False,
                "tool_chain": st.session_state.sar_tool_chain,
                "investigation_result": st.session_state.investigation_result,
                "rule_code": ctx.get("rule_code", ""),
                "clear_draft": True,
            }
            _rerun()


def render_sar_tab():
    pending = st.session_state.pop("_pending_sar_decision", None)
    if pending:
        with st.spinner("Recording analyst decision..."):
            ok, ref = _write_analyst_decision(
                session=get_active_session(),
                alert_id=pending["alert_id"],
                customer_id=pending["customer_id"],
                decision=pending["decision"],
                sar_filed=pending["sar_filed"],
                sar_recommended=pending["sar_recommended"],
                tool_chain=pending["tool_chain"],
                investigation_result=pending["investigation_result"],
                rule_code=pending["rule_code"],
            )
        if pending.get("clear_draft"):
            st.session_state.sar_draft = None
            st.session_state.sar_tool_chain = None
        if ok:
            if pending["decision"] == "CONFIRMED_FRAUD":
                st.session_state["_sar_msg"] = ("success", f"SAR filed. Decision logged: {ref}")
            elif pending["decision"] == "NEEDS_REVIEW":
                st.session_state["_sar_msg"] = ("success", f"SAR for alert {pending['alert_id']} returned for revision.")
            else:
                st.session_state["_sar_msg"] = ("success", f"SAR draft for alert {pending['alert_id']} discarded. Decision logged.")
        else:
            st.session_state["_sar_msg"] = ("error", f"Write-back error: {ref}")

    ctx = st.session_state.sar_alert_context

    if not ctx:
        section_card(
            '<strong>No alert selected for SAR drafting.</strong><br>'
            '<span style="color:#a0aec0;font-size:0.85rem">'
            "Run an investigation on the Investigation tab, then click "
            "<b>File SAR</b> to send context here.</span>"
        )
        return

    risk_val = f"{ctx['risk_score']:.3f}"
    section_card(
        f'<strong>SAR Drafting</strong> &nbsp;&middot;&nbsp; Alert <code>{html.escape(str(ctx["alert_id"]))}</code> '
        f'&nbsp;&middot;&nbsp; Customer <code>{html.escape(str(ctx["customer_id"]))}</code> '
        f'&nbsp;&middot;&nbsp; {html.escape(str(ctx["full_name"]))} &nbsp;&middot;&nbsp; Risk {badge(risk_val)}'
    )

    status_banner("DRAFT \u2014 REQUIRES LICENSED COMPLIANCE OFFICER REVIEW AND SIGN-OFF BEFORE FILING WITH FINCEN")

    run_sar_agent(ctx)
    render_sar_draft(ctx)

    if st.session_state.get("_sar_msg"):
        msg_type, msg_text = st.session_state["_sar_msg"]
        if msg_type == "success":
            st.success(msg_text)
        else:
            st.error(msg_text)
        st.session_state["_sar_msg"] = None


def main():
    st.set_page_config(
        page_title="Fraud Intelligence Solution",
        page_icon="\U0001f6e1\ufe0f",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    apply_theme()

    session = get_active_session()

    logo = session.file.get_stream(
        "@DEMO_DEV.PUBLIC.SHARED_ASSETS/_shared_theme/Mastech Digital-White 4.svg",
        decompress=False,
    ).read()
    logo_b64 = base64.b64encode(logo).decode()

    init_session_state()

    alerts_df = load_alerts(session)

    if alerts_df.empty:
        st.warning("No alerts found in GLD_ALERT_ENRICHMENT_WITH_SCORING.")
        st.stop()

    alert_ids = alerts_df["ALERT_ID"].tolist()

    st.markdown(
        f'<div class="app-header">'
        f'<div style="display:flex;align-items:center;gap:20px">'
        f'<img src="data:image/svg+xml;base64,{logo_b64}" height="40"/>'
        f'<div><h1>&#x1F6E1;&#xFE0F; Fraud Intelligence Solution</h1>'
        f'<p>AI-powered alert investigation &nbsp;&middot;&nbsp; SAR narrative drafting &nbsp;&middot;&nbsp; Powered by Snowflake Cortex Agents</p>'
        f'</div></div></div>',
        unsafe_allow_html=True,
    )

    alert_row, selected_alert_id, customer_id = render_alert_selector(alerts_df, alert_ids)

    cp_df = load_customer_profile(session, customer_id)
    vc_df = load_velocity(session, customer_id)
    cp = cp_df.iloc[0].to_dict() if not cp_df.empty else {}
    vc = vc_df.iloc[0].to_dict() if not vc_df.empty else {}

    tab_investigate, tab_sar, tab_governance = st.tabs(["Investigation", "SAR Drafting", "Governance"])

    with tab_investigate:
        render_investigation_tab(alert_row, selected_alert_id, customer_id, cp, vc)

    with tab_sar:
        render_sar_tab()

    with tab_governance:
        render_governance_tab(session)


main()
