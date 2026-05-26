{{
    config(
        materialized = 'view',
        tags = ['staging', 'orders']
    )
}}

with source as (
    select * from {{ source('tpch_raw', 'ORDERS') }}
),

renamed as (
    select
        order_id,
        customer_id,
        order_date,
        total_amount,
        upper(trim(status)) as status

    from source
),

validated as (
    select *
    from renamed
    where order_id is not null
      and customer_id is not null
)

select * from validated
