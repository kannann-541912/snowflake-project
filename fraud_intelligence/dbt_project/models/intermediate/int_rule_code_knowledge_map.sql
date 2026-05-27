{{
    config(
        materialized='table',
        alias='SLV_RULE_CODE_KNOWLEDGE_MAP',
        tags=['silver']
    )
}}

SELECT
    RULE_CODE,
    RULE_NAME,
    RULE_DESCRIPTION AS DESCRIPTION,
    RULE_CATEGORY AS CATEGORY,
    RISK_WEIGHT,
    IS_ACTIVE,
    CREATED_DATE,
    INGESTED_AT AS LOADED_AT
FROM {{ ref('stg_raw_rule_definitions') }}
