select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    DOC_ID as unique_field,
    count(*) as n_records

from DEMO_DEV.FRAUD_INTELLIGENCE.SLV_INVESTIGATION_KNOWLEDGE_BASE
where DOC_ID is not null
group by DOC_ID
having count(*) > 1



      
    ) dbt_internal_test