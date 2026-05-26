-- Example registration and activation flow for churn_risk v1.0.0.
-- Adjust database/schema names for your environment before execution.

USE DATABASE ML_STAGING;
USE SCHEMA MLOPS;

-- 1) Register the model version in the registry.
INSERT INTO MODEL_REGISTRY (
    MODEL_NAME,
    MODEL_VERSION,
    OWNER,
    RISK_TIER,
    STAGE,
    ARTIFACT_URI,
    FEATURE_CONTRACT_VERSION,
    TRAIN_DATA_WINDOW,
    METRICS,
    IS_ACTIVE
)
SELECT
    'churn_risk',
    'v1.0.0',
    'ml-retention-team',
    'medium',
    'staging',
    '@ML_MODEL_STAGE/churn_risk/v1.0.0/model.pkl',
    'customer_features_v3',
    '2025-01-01 to 2025-12-31',
    PARSE_JSON('{"auc_roc":0.86,"pr_auc":0.49,"p95_latency_ms":870}'),
    FALSE;

-- 2) Optional: deactivate older active versions before activation.
UPDATE MODEL_REGISTRY
SET IS_ACTIVE = FALSE
WHERE MODEL_NAME = 'churn_risk'
  AND MODEL_VERSION <> 'v1.0.0'
  AND IS_ACTIVE = TRUE;

-- 3) Activate this version.
UPDATE MODEL_REGISTRY
SET IS_ACTIVE = TRUE
WHERE MODEL_NAME = 'churn_risk'
  AND MODEL_VERSION = 'v1.0.0';

-- 4) Log deployment event.
INSERT INTO MODEL_DEPLOYMENT_EVENTS (
    MODEL_NAME,
    MODEL_VERSION,
    ENVIRONMENT,
    EVENT_TYPE,
    EVENT_STATUS,
    APPROVED_BY,
    DETAILS
)
SELECT
    'churn_risk',
    'v1.0.0',
    'staging',
    'deploy',
    'success',
    CURRENT_USER(),
    PARSE_JSON('{"change_ticket":"CHG-2026-0001","strategy":"10_percent_canary"}');
