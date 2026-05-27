{{
    config(
        materialized='view',
        tags=['staging']
    )
}}

SELECT
    CUSTOMER_ID,
    FULL_NAME,
    DATE_OF_BIRTH,
    EMAIL,
    PHONE,
    RISK_SEGMENT,
    KYC_COMPLETE,
    IS_SYNTHETIC_FLAG,
    IS_MERGER_DUP_FLAG,
    CUSTOMER_SINCE,
    ACCOUNT_COUNT,
    DATEDIFF(DAY, CUSTOMER_SINCE, CURRENT_DATE()) AS CUSTOMER_TENURE_DAYS,
    INGESTED_AT
FROM {{ source('fraud_intelligence_bronze', 'BRZ_RAW_CUSTOMERS') }}
WHERE CUSTOMER_ID IS NOT NULL
