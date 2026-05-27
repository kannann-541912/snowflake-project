
    
    

select
    ALERT_ID as unique_field,
    count(*) as n_records

from DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_RAW_ALERTS
where ALERT_ID is not null
group by ALERT_ID
having count(*) > 1


