{{
    config(
        materialized='table',
        alias='SLV_INVESTIGATION_KNOWLEDGE_BASE',
        tags=['silver']
    )
}}

SELECT
    DOC_ID,
    DOC_TITLE AS TITLE,
    DOC_CONTENT AS CONTENT,
    DOC_CATEGORY AS CATEGORY,
    EFFECTIVE_DATE,
    INGESTED_AT AS LOADED_AT
FROM {{ ref('stg_raw_investigation_docs') }}
