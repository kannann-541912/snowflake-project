select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select TARGET_LABEL
from DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ML_TRAINING_SET
where TARGET_LABEL is null



      
    ) dbt_internal_test