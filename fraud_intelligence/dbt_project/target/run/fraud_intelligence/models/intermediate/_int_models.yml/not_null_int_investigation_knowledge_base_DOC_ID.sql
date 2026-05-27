select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select DOC_ID
from DEMO_DEV.FRAUD_INTELLIGENCE.SLV_INVESTIGATION_KNOWLEDGE_BASE
where DOC_ID is null



      
    ) dbt_internal_test