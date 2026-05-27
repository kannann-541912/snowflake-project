SELECT CUSTOMER_ID
FROM {{ ref('gld_alert_enriched') }}
WHERE CUSTOMER_ID IS NULL
