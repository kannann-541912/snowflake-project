{{
    config(
        materialized='view',
        tags=['staging']
    )
}}

SELECT
    DOC_ID,
    DOC_TITLE,
    DOC_CONTENT,
    DOC_CATEGORY,
    EFFECTIVE_DATE,
    INGESTED_AT
FROM {{ source('fraud_intelligence_bronze', 'BRZ_RAW_INVESTIGATION_DOCS') }}
WHERE DOC_ID IS NOT NULL
