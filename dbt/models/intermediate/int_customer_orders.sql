{{
    config(
        materialized = 'ephemeral',
        tags = ['intermediate']
    )
}}

/*
  Joins customers and orders, computes per-customer order metrics.
  Ephemeral: inlined into downstream mart queries — not persisted as a table.
*/

with customers as (
    select * from {{ ref('stg_customers') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

customer_order_metrics as (
    select
        c.customer_id,
        c.customer_name,
        c.email,
        c.created_at                            as customer_since,
        count(o.order_id)                       as total_orders,
        coalesce(sum(o.total_amount), 0)        as lifetime_value,
        coalesce(avg(o.total_amount), 0)        as avg_order_value,
        min(o.order_date)                       as first_order_date,
        max(o.order_date)                       as last_order_date,
        count(case when o.status = 'CANCELLED'
                   then 1 end)                  as cancelled_orders,
        count(case when o.status = 'RETURNED'
                   then 1 end)                  as returned_orders

    from customers c
    left join orders o
        on c.customer_id = o.customer_id
    group by
        c.customer_id,
        c.customer_name,
        c.email,
        c.created_at
)

select * from customer_order_metrics
