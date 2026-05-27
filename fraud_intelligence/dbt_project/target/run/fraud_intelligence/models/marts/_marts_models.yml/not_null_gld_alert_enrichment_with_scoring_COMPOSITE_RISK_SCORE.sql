select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select COMPOSITE_RISK_SCORE
from DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHMENT_WITH_SCORING
where COMPOSITE_RISK_SCORE is null



      
    ) dbt_internal_test