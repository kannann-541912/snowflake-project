{{
    config(
        materialized='view',
        tags=['staging']
    )
}}

SELECT
    TRANSACTION_ID,
    CUSTOMER_ID,
    ACCOUNT_ID,
    TRANSACTION_DATE,
    TRANSACTION_AMOUNT,
    TRANSACTION_TYPE,
    MERCHANT_CATEGORY,
    CHANNEL,
    MERCHANT_NAME,
    MERCHANT_COUNTRY,
    INGESTED_AT
FROM {{ source('fraud_intelligence_bronze', 'BRZ_RAW_TRANSACTIONS') }}
WHERE TRANSACTION_ID IS NOT NULL
