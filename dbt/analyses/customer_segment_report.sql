-- Analysis: Customer segment distribution
-- Run with: dbt compile --select analyses/customer_segment_report
-- Then copy the compiled SQL from target/compiled/ to run against Snowflake.

select
    customer_segment,
    count(*)                                          as customer_count,
    round(count(*) * 100.0 / sum(count(*)) over (), 2) as pct_of_total,
    avg(lifetime_value)                               as avg_lifetime_value,
    avg(total_orders)                                 as avg_orders,
    avg(avg_order_value)                              as avg_order_value

from {{ ref('fct_customer_orders') }}
group by customer_segment
order by avg_lifetime_value desc
