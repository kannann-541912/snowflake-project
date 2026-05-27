select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    



select EVENT_ID
from DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_RAW_VELOCITY_EVENTS
where EVENT_ID is null



      
    ) dbt_internal_test