{% snapshot customers_snapshot %}

{{
    config(
        target_schema = 'snapshots',
        unique_key = 'customer_id',
        strategy = 'timestamp',
        updated_at = 'created_at',
        invalidate_hard_deletes = True
    )
}}

/*
  Type-2 SCD snapshot of the CUSTOMERS source table.
  Captures historical changes to customer name and email.
  Uses Snowflake CHANGE_TRACKING under the hood.
*/

select
    customer_id,
    customer_name,
    email,
    created_at

from {{ ref('stg_customers') }}

{% endsnapshot %}
