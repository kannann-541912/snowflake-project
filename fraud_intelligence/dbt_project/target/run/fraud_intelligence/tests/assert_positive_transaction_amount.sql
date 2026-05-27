select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      SELECT TRANSACTION_ID, TRANSACTION_AMOUNT
FROM DEMO_DEV.FRAUD_INTELLIGENCE.SLV_FRAUD_FEATURES
WHERE TRANSACTION_AMOUNT <= 0
      
    ) dbt_internal_test