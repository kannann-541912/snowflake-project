-- Example registration and controlled activation for fraud_risk v1.0.0.
-- This pattern expects two APPROVE decisions in MODEL_APPROVALS before production activation.

USE DATABASE ML_STAGING;
USE SCHEMA MLOPS;

-- 1) Register model version in staging registry.
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
    'fraud_risk',
    'v1.0.0',
    'ml-fraud-team',
    'high',
    'staging',
    '@ML_MODEL_STAGE/fraud_risk/v1.0.0/model.pkl',
    'fraud_features_v5',
    '2025-04-01 to 2026-03-31',
    PARSE_JSON('{"auc_pr":0.75,"roc_auc":0.93,"p95_latency_ms":260}'),
    FALSE;

-- 2) Record deploy event in staging.
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
    'fraud_risk',
    'v1.0.0',
    'staging',
    'deploy',
    'success',
    CURRENT_USER(),
    PARSE_JSON('{"change_ticket":"CHG-2026-0100","strategy":"5_percent_canary"}');

-- 3) Example production activation (run in ML_PROD.MLOPS) only after dual approval.
-- USE DATABASE ML_PROD;
-- USE SCHEMA MLOPS;
--
-- UPDATE MODEL_REGISTRY
-- SET IS_ACTIVE = TRUE, STAGE = 'prod'
-- WHERE MODEL_NAME = 'fraud_risk'
--   AND MODEL_VERSION = 'v1.0.0'
--   AND (
--     SELECT COUNT(*)
--     FROM MODEL_APPROVALS
--     WHERE MODEL_NAME = 'fraud_risk'
--       AND MODEL_VERSION = 'v1.0.0'
--       AND ENVIRONMENT = 'prod'
--       AND DECISION = 'APPROVE'
--   ) >= 2;
