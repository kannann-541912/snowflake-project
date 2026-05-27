select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

with all_values as (

    select
        RISK_SEGMENT as value_field,
        count(*) as n_records

    from DEMO_DEV.FRAUD_INTELLIGENCE.GLD_CUSTOMER_PROFILE
    group by RISK_SEGMENT

)

select *
from all_values
where value_field not in (
    'HIGH','MEDIUM','LOW','CRITICAL'
)



      
    ) dbt_internal_test