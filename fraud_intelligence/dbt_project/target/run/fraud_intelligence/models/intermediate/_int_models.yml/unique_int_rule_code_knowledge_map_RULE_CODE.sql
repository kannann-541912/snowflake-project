select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    RULE_CODE as unique_field,
    count(*) as n_records

from DEMO_DEV.FRAUD_INTELLIGENCE.SLV_RULE_CODE_KNOWLEDGE_MAP
where RULE_CODE is not null
group by RULE_CODE
having count(*) > 1



      
    ) dbt_internal_test