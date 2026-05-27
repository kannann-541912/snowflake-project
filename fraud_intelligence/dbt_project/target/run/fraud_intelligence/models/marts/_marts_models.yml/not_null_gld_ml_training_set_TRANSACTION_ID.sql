select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select TRANSACTION_ID
from DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ML_TRAINING_SET
where TRANSACTION_ID is null



      
    ) dbt_internal_test