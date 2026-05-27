select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select TRANSACTION_AMOUNT
from DEMO_DEV.FRAUD_INTELLIGENCE.SLV_FRAUD_FEATURES
where TRANSACTION_AMOUNT is null



      
    ) dbt_internal_test