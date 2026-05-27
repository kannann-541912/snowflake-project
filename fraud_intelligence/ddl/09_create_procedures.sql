USE ROLE AGENT_DEMO_ROLE;
USE WAREHOUSE AGENT_DEMO_WH;
USE SCHEMA DEMO_DEV.FRAUD_INTELLIGENCE;

CREATE OR REPLACE PROCEDURE DEMO_DEV.FRAUD_INTELLIGENCE.SCORE_TRANSACTION(ALERT_ID VARCHAR)
RETURNS OBJECT
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python', 'snowflake-ml-python', 'pandas', 'xgboost')
HANDLER = 'score_handler'
EXECUTE AS OWNER
AS $$
import pandas as pd
import json
import time
from datetime import datetime, timezone
import snowflake.snowpark as sp
from snowflake.snowpark.functions import col, lit
from snowflake.ml.registry import Registry

FEATURE_COLUMNS = [
    "TRANSACTION_AMOUNT", "ACCOUNT_AGE_DAYS", "CREDIT_LIMIT", "CURRENT_BALANCE",
    "UTILIZATION_RATIO", "ADDRESS_CHANGE_COUNT", "CUSTOMER_TENURE_DAYS",
    "PRIOR_ALERT_COUNT_CUSTOMER", "ALERT_WITHIN_7D",
    "TXN_COUNT_1H", "TXN_COUNT_24H", "TXN_AMOUNT_1H", "TXN_AMOUNT_24H",
    "DISTINCT_MERCHANTS_24H", "KYC_COMPLETE", "IS_SYNTHETIC_FLAG", "IS_MERGER_DUP_FLAG",
    "TRANSACTION_TYPE_CASH_ADVANCE", "TRANSACTION_TYPE_PAYMENT",
    "TRANSACTION_TYPE_PURCHASE", "TRANSACTION_TYPE_TRANSFER",
    "MERCHANT_CATEGORY_CASH", "MERCHANT_CATEGORY_DINING", "MERCHANT_CATEGORY_GAS",
    "MERCHANT_CATEGORY_GROCERY", "MERCHANT_CATEGORY_HEALTHCARE",
    "MERCHANT_CATEGORY_ONLINE", "MERCHANT_CATEGORY_RETAIL", "MERCHANT_CATEGORY_TRAVEL",
    "CHANNEL_ATM", "CHANNEL_BRANCH", "CHANNEL_MOBILE", "CHANNEL_ONLINE",
    "ACCOUNT_TYPE_CREDIT", "ACCOUNT_TYPE_SAVINGS",
    "RISK_SEGMENT_LOW", "RISK_SEGMENT_MEDIUM"
]

def _get_active_model_version(session):
    rows = session.sql(
        "SELECT MODEL_VERSION FROM DEMO_DEV.FRAUD_INTELLIGENCE.SLV_FRAUD_MODEL_METADATA "
        "WHERE MODEL_STATUS = 'ACTIVE' ORDER BY LAST_TRAINED_AT DESC LIMIT 1"
    ).collect()
    return rows[0]["MODEL_VERSION"] if rows else "V1"

def _build_features(row: dict, vc: dict) -> pd.DataFrame:
    fv = {c: 0.0 for c in FEATURE_COLUMNS}
    fv["TRANSACTION_AMOUNT"]        = float(row.get("TRANSACTION_AMOUNT") or 0)
    fv["ACCOUNT_AGE_DAYS"]          = float(row.get("ACCOUNT_AGE_DAYS") or 0)
    fv["CREDIT_LIMIT"]              = float(row.get("CREDIT_LIMIT") or 0)
    fv["CURRENT_BALANCE"]           = float(row.get("CURRENT_BALANCE") or 0)
    fv["UTILIZATION_RATIO"]         = float(row.get("UTILIZATION_RATIO") or 0)
    fv["ADDRESS_CHANGE_COUNT"]      = float(row.get("ADDRESS_CHANGE_COUNT") or 0)
    fv["CUSTOMER_TENURE_DAYS"]      = float(row.get("CUSTOMER_TENURE_DAYS") or 0)
    fv["PRIOR_ALERT_COUNT_CUSTOMER"]= float(row.get("PRIOR_ALERT_COUNT_CUSTOMER") or 0)
    fv["ALERT_WITHIN_7D"]           = float(row.get("ALERT_WITHIN_7D") or 0)
    fv["TXN_COUNT_1H"]              = float(vc.get("TXN_COUNT_1H") or 0)
    fv["TXN_COUNT_24H"]             = float(vc.get("TXN_COUNT_24H") or 0)
    fv["TXN_AMOUNT_1H"]             = float(vc.get("TXN_AMOUNT_1H") or 0)
    fv["TXN_AMOUNT_24H"]            = float(vc.get("TXN_AMOUNT_24H") or 0)
    fv["DISTINCT_MERCHANTS_24H"]    = float(vc.get("DISTINCT_MERCHANTS_24H") or 0)
    fv["KYC_COMPLETE"]              = 1.0 if row.get("KYC_COMPLETE") else 0.0
    fv["IS_SYNTHETIC_FLAG"]         = 1.0 if row.get("IS_SYNTHETIC_FLAG") else 0.0
    fv["IS_MERGER_DUP_FLAG"]        = 1.0 if row.get("IS_MERGER_DUP_FLAG") else 0.0
    txn_type = str(row.get("TRANSACTION_TYPE") or "")
    fv[f"TRANSACTION_TYPE_{txn_type}"] = 1.0 if f"TRANSACTION_TYPE_{txn_type}" in fv else 0.0
    merchant = str(row.get("MERCHANT_CATEGORY") or "")
    fv[f"MERCHANT_CATEGORY_{merchant}"] = 1.0 if f"MERCHANT_CATEGORY_{merchant}" in fv else 0.0
    channel = str(row.get("CHANNEL") or "")
    fv[f"CHANNEL_{channel}"] = 1.0 if f"CHANNEL_{channel}" in fv else 0.0
    acct = str(row.get("ACCOUNT_TYPE") or "")
    fv[f"ACCOUNT_TYPE_{acct}"] = 1.0 if f"ACCOUNT_TYPE_{acct}" in fv else 0.0
    risk = str(row.get("RISK_SEGMENT") or "")
    fv[f"RISK_SEGMENT_{risk}"] = 1.0 if f"RISK_SEGMENT_{risk}" in fv else 0.0
    return pd.DataFrame([{c: fv.get(c, 0.0) for c in FEATURE_COLUMNS}])

def _score_single(session, alert_id: str, model_version: str) -> dict:
    rows = session.sql(
        f"SELECT f.* "
        f"FROM DEMO_DEV.FRAUD_INTELLIGENCE.SLV_FRAUD_FEATURES f "
        f"WHERE f.TRANSACTION_ID IN ("
        f"  SELECT TRANSACTION_ID FROM DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_RAW_ALERTS "
        f"  WHERE ALERT_ID = '{alert_id}' LIMIT 1) LIMIT 1"
    ).collect()
    if not rows:
        rows = session.sql(
            f"SELECT f.* "
            f"FROM DEMO_DEV.FRAUD_INTELLIGENCE.SLV_FRAUD_FEATURES f "
            f"WHERE f.CUSTOMER_ID IN ("
            f"  SELECT CUSTOMER_ID FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED "
            f"  WHERE ALERT_ID = '{alert_id}' LIMIT 1) LIMIT 1"
        ).collect()
    if not rows:
        return {"fraud_probability": 0.0, "risk_tier": "LOW"}
    row_data = rows[0].as_dict()
    input_df = _build_features(row_data, row_data)
    registry = Registry(session=session, database_name="DEMO_DEV", schema_name="FRAUD_INTELLIGENCE")
    mv = registry.get_model("FRAUD_DETECTION_MODEL").version(model_version)
    prediction = mv.run(input_df, function_name="predict_proba")
    fraud_prob = float(prediction.iloc[0, 1])
    if fraud_prob >= 0.8:   risk_tier = "CRITICAL"
    elif fraud_prob >= 0.5: risk_tier = "HIGH"
    elif fraud_prob >= 0.3: risk_tier = "MEDIUM"
    else:                   risk_tier = "LOW"
    return {"fraud_probability": round(fraud_prob, 6), "risk_tier": risk_tier}

def _write_score_back(session, alert_id: str, fraud_prob: float, risk_tier: str, model_version: str):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    session.sql(
        f"UPDATE DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED "
        f"SET ML_FRAUD_SCORE = {fraud_prob}, ML_RISK_TIER = '{risk_tier}', "
        f"ML_MODEL_VERSION = '{model_version}', ML_SCORED_AT = '{now}' "
        f"WHERE ALERT_ID = '{alert_id}'"
    ).collect()

def score_handler(session: sp.Session, alert_id: str):
    model_version = _get_active_model_version(session)

    # ── BATCH PATH ────────────────────────────────────────────────────────────
    # Called by TASK_ML_SCORE_ALERTS after every ETL run.
    # Scores all unscored alerts in GLD_ALERT_ENRICHED and writes back.
    if alert_id.upper() == "BATCH":
        unscored = session.sql(
            "SELECT ALERT_ID FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED "
            "WHERE ML_FRAUD_SCORE IS NULL"
        ).collect()
        scored = 0
        errors = 0
        for r in unscored:
            try:
                result = _score_single(session, r["ALERT_ID"], model_version)
                _write_score_back(session, r["ALERT_ID"],
                                  result["fraud_probability"], result["risk_tier"],
                                  model_version)
                scored += 1
            except Exception:
                errors += 1
        return {"mode": "BATCH", "scored": scored, "errors": errors,
                "model_version": model_version}

    # ── ON-DEMAND PATH ────────────────────────────────────────────────────────
    # Called by FRAUD_TRIAGE_AGENT FraudScorer tool for a specific alert.

    # Step 1: Fast lookup — check if already scored by inference pipeline
    pre_scored = session.sql(
        f"SELECT ML_FRAUD_SCORE, ML_RISK_TIER, ML_MODEL_VERSION "
        f"FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED "
        f"WHERE ALERT_ID = '{alert_id}' AND ML_FRAUD_SCORE IS NOT NULL LIMIT 1"
    ).collect()

    if pre_scored:
        row = pre_scored[0].as_dict()
        return {
            "alert_id": alert_id,
            "fraud_probability": float(row["ML_FRAUD_SCORE"]),
            "risk_tier": row["ML_RISK_TIER"],
            "model_version": row["ML_MODEL_VERSION"],
            "scored_by": "PRE_SCORED_PIPELINE"
        }

    # Step 2: Net-new alert — trigger inference pipeline task and wait (max 45s)
    # The pipeline will score this alert and all other unscored alerts.
    try:
        session.sql(
            "EXECUTE TASK DEMO_DEV.FRAUD_INTELLIGENCE.TASK_ML_INFERENCE_ROOT"
        ).collect()

        for _ in range(9):
            time.sleep(5)
            refreshed = session.sql(
                f"SELECT ML_FRAUD_SCORE, ML_RISK_TIER, ML_MODEL_VERSION "
                f"FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED "
                f"WHERE ALERT_ID = '{alert_id}' AND ML_FRAUD_SCORE IS NOT NULL LIMIT 1"
            ).collect()
            if refreshed:
                row = refreshed[0].as_dict()
                return {
                    "alert_id": alert_id,
                    "fraud_probability": float(row["ML_FRAUD_SCORE"]),
                    "risk_tier": row["ML_RISK_TIER"],
                    "model_version": row["ML_MODEL_VERSION"],
                    "scored_by": "PIPELINE_TRIGGERED"
                }
    except Exception:
        pass

    # Step 3: Fallback — pipeline timed out or task unavailable.
    # Run proper real-time model inference for this specific alert (not random).
    result = _score_single(session, alert_id, model_version)
    _write_score_back(session, alert_id, result["fraud_probability"],
                      result["risk_tier"], model_version)
    return {
        "alert_id": alert_id,
        "fraud_probability": result["fraud_probability"],
        "risk_tier": result["risk_tier"],
        "model_version": model_version,
        "scored_by": "REALTIME_FALLBACK"
    }
$$;
