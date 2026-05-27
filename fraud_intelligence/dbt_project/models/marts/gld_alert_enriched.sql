{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key='ALERT_ID',
        alias='GLD_ALERT_ENRICHED',
        tags=['gold']
    )
}}

WITH deduped AS (
    SELECT
        a.ALERT_ID,
        a.CUSTOMER_ID,
        a.ALERT_DATE,
        a.RULE_CODE,
        a.RULE_DESCRIPTION,
        a.ALERT_RISK_SCORE,
        a.ALERT_STATUS,
        a.ANALYST_ID,
        a.DISPOSITION,
        a.SAR_FILED,
        CASE
            WHEN a.DISPOSITION IN ('FRAUD_CONFIRMED', 'SAR_FILED', 'CONFIRMED_FRAUD') THEN TRUE
            WHEN a.SAR_FILED = TRUE THEN TRUE
            ELSE FALSE
        END AS IS_FRAUD_DERIVED,
        CAST(NULL AS NUMBER(7,6))    AS ML_FRAUD_SCORE,
        CAST(NULL AS VARCHAR(10))    AS ML_RISK_TIER,
        CAST(NULL AS VARCHAR(50))    AS ML_MODEL_VERSION,
        CAST(NULL AS TIMESTAMP_LTZ) AS ML_SCORED_AT,
        a.INGESTED_AT AS DBT_LOADED_AT,
        ROW_NUMBER() OVER (PARTITION BY a.ALERT_ID ORDER BY a.INGESTED_AT DESC) AS rn
    FROM {{ ref('stg_raw_alerts') }} a
)

SELECT
    ALERT_ID, CUSTOMER_ID, ALERT_DATE, RULE_CODE, RULE_DESCRIPTION,
    ALERT_RISK_SCORE, ALERT_STATUS, ANALYST_ID, DISPOSITION, SAR_FILED,
    IS_FRAUD_DERIVED, ML_FRAUD_SCORE, ML_RISK_TIER, ML_MODEL_VERSION,
    ML_SCORED_AT, DBT_LOADED_AT
FROM deduped
WHERE rn = 1
{% if is_incremental() %}
  AND ALERT_ID NOT IN (SELECT ALERT_ID FROM {{ this }} WHERE ML_FRAUD_SCORE IS NOT NULL)
{% endif %}
