SELECT ALERT_ID, COUNT(*) AS CNT
FROM {{ ref('gld_alert_enriched') }}
GROUP BY ALERT_ID
HAVING COUNT(*) > 1
