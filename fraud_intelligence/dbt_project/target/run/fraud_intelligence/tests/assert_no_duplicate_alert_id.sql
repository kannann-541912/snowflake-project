select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      SELECT ALERT_ID, COUNT(*) AS CNT
FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED
GROUP BY ALERT_ID
HAVING COUNT(*) > 1
      
    ) dbt_internal_test