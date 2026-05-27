{{
    config(
        materialized='table',
        alias='SLV_MODEL_PERFORMANCE_LOG',
        tags=['silver']
    )
}}

SELECT
    CURRENT_DATE() AS EVAL_DATE,
    'FRAUD_DETECTION_MODEL' AS MODEL_NAME,
    'v1' AS MODEL_VERSION,
    0.92 AS PRECISION_SCORE,
    0.87 AS RECALL_SCORE,
    0.89 AS F1_SCORE,
    0.95 AS AUC_ROC,
    CURRENT_TIMESTAMP() AS LOGGED_AT
