
    
    

select
    CUSTOMER_ID as unique_field,
    count(*) as n_records

from DEMO_DEV.FRAUD_INTELLIGENCE.GLD_CUSTOMER_PROFILE
where CUSTOMER_ID is not null
group by CUSTOMER_ID
having count(*) > 1


