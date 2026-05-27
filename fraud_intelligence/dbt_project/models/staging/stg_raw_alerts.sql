{{
    config(
        materialized='view',
        tags=['staging']
    )
}}

SELECT
    ALERT_ID,
    CUSTOMER_ID,
    ALERT_DATE,
    RULE_CODE,
    RULE_DESCRIPTION,
    ALERT_RISK_SCORE,
    ALERT_STATUS,
    ANALYST_ID,
    DISPOSITION,
    SAR_FILED,
    INGESTED_AT
FROM {{ source('fraud_intelligence_bronze', 'BRZ_RAW_ALERTS') }}
WHERE ALERT_ID IS NOT NULL
