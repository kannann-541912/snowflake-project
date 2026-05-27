select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select ALERT_RISK_SCORE
from DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED
where ALERT_RISK_SCORE is null



      
    ) dbt_internal_test