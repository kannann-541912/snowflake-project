select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select ALERT_ID
from DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED
where ALERT_ID is null



      
    ) dbt_internal_test