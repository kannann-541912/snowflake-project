select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      SELECT CUSTOMER_ID
FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED
WHERE CUSTOMER_ID IS NULL
      
    ) dbt_internal_test