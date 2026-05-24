{{
    config(
        materialized = 'view',
        tags = ['staging', 'customers']
    )
}}

with source as (
    select * from {{ source('tpch_raw', 'CUSTOMERS') }}
),

renamed as (
    select
        customer_id,
        trim(name)         as customer_name,
        lower(trim(email)) as email,
        created_at

    from source
),

validated as (
    select *
    from renamed
    -- Defensive filter: drop rows with null PKs (should be caught by source tests)
    where customer_id is not null
)

select * from validated
