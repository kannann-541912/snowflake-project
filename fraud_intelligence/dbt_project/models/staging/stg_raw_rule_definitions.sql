{{
    config(
        materialized='view',
        tags=['staging']
    )
}}

SELECT
    RULE_CODE,
    RULE_NAME,
    RULE_DESCRIPTION,
    RULE_CATEGORY,
    RISK_WEIGHT,
    IS_ACTIVE,
    CREATED_DATE,
    INGESTED_AT
FROM {{ source('fraud_intelligence_bronze', 'BRZ_RAW_RULE_DEFINITIONS') }}
WHERE RULE_CODE IS NOT NULL
