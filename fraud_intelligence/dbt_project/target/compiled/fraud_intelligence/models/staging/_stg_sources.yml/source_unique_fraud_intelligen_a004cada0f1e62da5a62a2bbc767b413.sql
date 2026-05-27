
    
    

select
    RULE_CODE as unique_field,
    count(*) as n_records

from DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_RAW_RULE_DEFINITIONS
where RULE_CODE is not null
group by RULE_CODE
having count(*) > 1


