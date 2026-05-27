select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
    

select
    ALERT_ID as unique_field,
    count(*) as n_records

from DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_RAW_ALERTS
where ALERT_ID is not null
group by ALERT_ID
having count(*) > 1



      
    ) dbt_internal_test