{{
    config(
        materialized = 'incremental',
        unique_key = 'customer_id',
        incremental_strategy = 'merge',
        cluster_by = ['last_order_date'],
        tags = ['marts', 'customers'],
        on_schema_change = 'sync_all_columns'
    )
}}

/*
  Fact table: customer order summary mart.
  Replaces the hand-crafted CUSTOMER_ORDER_SUMMARY view — this is the
  authoritative source for the Cortex Agent and Streamlit dashboard.

  Incremental strategy: MERGE on customer_id so updates are idempotent.
  Clustered by last_order_date for efficient time-range scans.
*/

with base as (
    select * from {{ ref('int_customer_orders') }}

    {% if is_incremental() %}
    -- On incremental runs, re-process customers whose last_order_date changed
    -- within the lookback window to catch late-arriving order data.
    where last_order_date >= dateadd(
        hour,
        -{{ var('incremental_lookback_hours', 48) }},
        current_timestamp()
    )
    or customer_id in (
        select customer_id
        from {{ this }}
        where last_order_date >= dateadd(
            hour,
            -{{ var('incremental_lookback_hours', 48) }},
            current_timestamp()
        )
    )
    {% endif %}
),

enriched as (
    select
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_sk,
        customer_id,
        customer_name,
        email,
        customer_since,
        total_orders,
        lifetime_value,
        avg_order_value,
        first_order_date,
        last_order_date,
        cancelled_orders,
        returned_orders,
        -- Derived metrics
        case
            when total_orders = 0                    then 'NO_ORDERS'
            when last_order_date >= current_date - 30 then 'ACTIVE'
            when last_order_date >= current_date - 90 then 'AT_RISK'
            else 'LAPSED'
        end                                          as customer_segment,
        round(
            cancelled_orders * 100.0 / nullif(total_orders, 0), 2
        )                                            as cancellation_rate_pct,
        current_timestamp()                          as dbt_updated_at

    from base
)

select * from enriched
