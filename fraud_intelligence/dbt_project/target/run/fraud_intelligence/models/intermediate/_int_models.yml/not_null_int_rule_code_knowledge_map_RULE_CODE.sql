select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select RULE_CODE
from DEMO_DEV.FRAUD_INTELLIGENCE.SLV_RULE_CODE_KNOWLEDGE_MAP
where RULE_CODE is null



      
    ) dbt_internal_test