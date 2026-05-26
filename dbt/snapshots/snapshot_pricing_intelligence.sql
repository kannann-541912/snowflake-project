{% snapshot snapshot_pricing_intelligence %}

{{
    config(
        target_database='DEMO_DEV',
        target_schema='RETAIL_CATEGORY_ANALYTICS_AGENT',
        unique_key='SKU_ID',
        strategy='check',
        check_cols=[
            'OUR_CURRENT_PRICE',
            'PRIMARY_COMPETITOR_PRICE',
            'OVERALL_COMPETITIVE_POSITIONING_STATUS',
            'CURRENT_STOCK_LEVEL'
        ]
    )
}}

SELECT
    SKU_ID,
    PRODUCT_NAME,
    CATEGORY,
    BRAND,
    OUR_CURRENT_PRICE,
    OUR_COST_PRICE,
    OUR_MARGIN_PERCENTAGE,
    PRIMARY_COMPETITOR_NAME,
    PRIMARY_COMPETITOR_PRICE,
    PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT,
    OVERALL_COMPETITIVE_POSITIONING_STATUS,
    CURRENT_STOCK_LEVEL,
    STOCK_AVAILABILITY_STATUS,
    CORTEX_AI_RECOMMENDED_ACTION_TYPE
FROM {{ source('retail_category_analytics', 'GOLD_SKU_PRICING_INTELLIGENCE') }}

{% endsnapshot %}
