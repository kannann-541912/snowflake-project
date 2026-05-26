-- ============================================================
-- Stored Procedures — SQL (Imperative — CREATE OR REPLACE)
-- Schema: DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT
-- These are imperative objects deployed via CI.
-- DCM does not manage procedures.
-- ============================================================

CREATE OR REPLACE PROCEDURE DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.EXECUTE_SKU_ACTION(
    P_ACTION_TYPE VARCHAR,
    P_SKU_ID VARCHAR,
    P_REASON VARCHAR DEFAULT NULL,
    P_NEW_VALUE VARCHAR DEFAULT NULL
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
COMMENT = 'Executes a SKU-level action (REPRICE, REPLENISH, MONITOR, ESCALATE) and logs to audit trail'
AS
$$
DECLARE
    v_product_name VARCHAR;
    v_current_value VARCHAR;
    v_action_upper VARCHAR;
    v_audit_id VARCHAR;
    v_params VARCHAR;
    v_username VARCHAR;
BEGIN
    v_action_upper := UPPER(:P_ACTION_TYPE);

    IF (:v_action_upper NOT IN ('REPRICE', 'REPLENISH', 'MONITOR', 'ESCALATE')) THEN
        RETURN '{"status": "ERROR", "message": "Invalid action type. Must be one of: REPRICE, REPLENISH, MONITOR, ESCALATE"}';
    END IF;

    SELECT PRODUCT_NAME INTO :v_product_name
    FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_SKU_PRICING_INTELLIGENCE
    WHERE SKU_ID = :P_SKU_ID;

    IF (:v_product_name IS NULL) THEN
        RETURN '{"status": "ERROR", "message": "SKU not found: ' || :P_SKU_ID || '"}';
    END IF;

    IF (:v_action_upper = 'REPRICE') THEN
        SELECT OUR_CURRENT_PRICE::VARCHAR INTO :v_current_value
        FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_SKU_PRICING_INTELLIGENCE
        WHERE SKU_ID = :P_SKU_ID;
    ELSEIF (:v_action_upper = 'REPLENISH') THEN
        SELECT CURRENT_STOCK_LEVEL::VARCHAR INTO :v_current_value
        FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_SKU_PRICING_INTELLIGENCE
        WHERE SKU_ID = :P_SKU_ID;
    ELSE
        SELECT OVERALL_COMPETITIVE_POSITIONING_STATUS INTO :v_current_value
        FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_SKU_PRICING_INTELLIGENCE
        WHERE SKU_ID = :P_SKU_ID;
    END IF;

    v_audit_id := UUID_STRING();
    v_params := '{"action_type": "' || :v_action_upper || '", "new_value": "' || COALESCE(:P_NEW_VALUE, '') || '", "reason": "' || COALESCE(:P_REASON, '') || '"}';
    v_username := COALESCE(CURRENT_USER(), 'STREAMLIT_APP_USER');

    INSERT INTO DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_ACTION_EXECUTION_AUDIT (
        AUDIT_RECORD_ID, ACTION_TIMESTAMP, SNOWFLAKE_USER_WHO_EXECUTED_ACTION, SNOWFLAKE_QUERY_ID,
        ACTION_TYPE, SKU_ID, PRODUCT_NAME, ACTION_INPUT_PARAMETERS,
        VALUE_BEFORE_ACTION, VALUE_AFTER_ACTION, ACTION_REASON_OR_JUSTIFICATION,
        EXECUTION_STATUS, SYSTEM_RESPONSE_MESSAGE, WAS_THIS_ACTION_AI_SUGGESTED, IS_ROLLBACK_POSSIBLE
    )
    SELECT
        :v_audit_id, CURRENT_TIMESTAMP(), :v_username, LAST_QUERY_ID(),
        :v_action_upper, :P_SKU_ID, :v_product_name, PARSE_JSON(:v_params),
        :v_current_value, COALESCE(:P_NEW_VALUE, 'PENDING'),
        COALESCE(:P_REASON, 'Action initiated via AI Agent'),
        'SUCCESS', :v_action_upper || ' action recorded for ' || :v_product_name,
        TRUE, CASE WHEN :v_action_upper IN ('REPRICE', 'REPLENISH') THEN TRUE ELSE FALSE END;

    RETURN '{"status": "SUCCESS", "audit_id": "' || :v_audit_id || '", "action": "' || :v_action_upper || '", "sku_id": "' || :P_SKU_ID || '", "product": "' || :v_product_name || '", "previous_value": "' || COALESCE(:v_current_value, 'N/A') || '", "new_value": "' || COALESCE(:P_NEW_VALUE, 'PENDING') || '", "message": "' || :v_action_upper || ' action successfully recorded."}';
END;
$$;

CREATE OR REPLACE PROCEDURE DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GET_CATEGORY_HEALTH(
    P_CATEGORY VARCHAR DEFAULT NULL
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
COMMENT = 'Returns category-level health KPIs as JSON. Pass NULL for all categories or a specific category name.'
AS
$$
DECLARE
    result VARCHAR;
BEGIN
    IF (:P_CATEGORY IS NULL) THEN
        SELECT ARRAY_AGG(OBJECT_CONSTRUCT(
            'category', CATEGORY,
            'total_active_skus', TOTAL_ACTIVE_SKUS_IN_CATEGORY,
            'overpriced_skus', COUNT_OVERPRICED_SKUS,
            'underpriced_skus', COUNT_UNDERPRICED_SKUS,
            'at_parity_skus', COUNT_AT_PRICE_PARITY_SKUS,
            'out_of_stock_skus', COUNT_OUT_OF_STOCK_SKUS,
            'low_stock_skus', COUNT_LOW_STOCK_SKUS,
            'avg_margin_pct', ROUND(AVERAGE_MARGIN_PERCENTAGE, 2),
            'inventory_value_usd', ROUND(TOTAL_INVENTORY_RETAIL_VALUE_USD, 2),
            'skus_needing_price_action', COUNT_SKUS_NEEDING_PRICE_ACTION,
            'skus_needing_replenishment', COUNT_SKUS_NEEDING_REPLENISHMENT,
            'last_refreshed', TO_VARCHAR(GOLD_LAST_REFRESHED_AT, 'YYYY-MM-DD HH24:MI:SS')
        ))::VARCHAR INTO :result
        FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_CATEGORY_PERFORMANCE_SUMMARY;
    ELSE
        SELECT ARRAY_AGG(OBJECT_CONSTRUCT(
            'category', CATEGORY,
            'total_active_skus', TOTAL_ACTIVE_SKUS_IN_CATEGORY,
            'overpriced_skus', COUNT_OVERPRICED_SKUS,
            'underpriced_skus', COUNT_UNDERPRICED_SKUS,
            'at_parity_skus', COUNT_AT_PRICE_PARITY_SKUS,
            'out_of_stock_skus', COUNT_OUT_OF_STOCK_SKUS,
            'low_stock_skus', COUNT_LOW_STOCK_SKUS,
            'avg_margin_pct', ROUND(AVERAGE_MARGIN_PERCENTAGE, 2),
            'inventory_value_usd', ROUND(TOTAL_INVENTORY_RETAIL_VALUE_USD, 2),
            'skus_needing_price_action', COUNT_SKUS_NEEDING_PRICE_ACTION,
            'skus_needing_replenishment', COUNT_SKUS_NEEDING_REPLENISHMENT,
            'last_refreshed', TO_VARCHAR(GOLD_LAST_REFRESHED_AT, 'YYYY-MM-DD HH24:MI:SS')
        ))::VARCHAR INTO :result
        FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_CATEGORY_PERFORMANCE_SUMMARY
        WHERE CATEGORY = :P_CATEGORY;
    END IF;

    RETURN COALESCE(:result, '[]');
END;
$$;

CREATE OR REPLACE PROCEDURE DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GET_PRICING_ALERTS(
    P_CATEGORY VARCHAR DEFAULT NULL,
    P_LIMIT NUMBER(38,0) DEFAULT 20
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
COMMENT = 'Returns SKUs requiring immediate price review as JSON. Optionally filter by category.'
AS
$$
DECLARE
    result VARCHAR;
    alert_count NUMBER;
BEGIN
    IF (:P_CATEGORY IS NULL) THEN
        SELECT COUNT(*) INTO :alert_count
        FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_SKU_PRICING_INTELLIGENCE
        WHERE REQUIRES_IMMEDIATE_PRICE_REVIEW = TRUE;

        LET rs RESULTSET := (
            SELECT
                SKU_ID, PRODUCT_NAME, CATEGORY, BRAND, OUR_CURRENT_PRICE,
                PRIMARY_COMPETITOR_NAME, PRIMARY_COMPETITOR_PRICE,
                PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT AS PRICE_GAP_PCT,
                STOCK_AVAILABILITY_STATUS AS STOCK_STATUS,
                CORTEX_AI_RECOMMENDATION_SUMMARY AS AI_RECOMMENDATION,
                CORTEX_AI_RECOMMENDED_ACTION_TYPE AS AI_ACTION_TYPE
            FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_SKU_PRICING_INTELLIGENCE
            WHERE REQUIRES_IMMEDIATE_PRICE_REVIEW = TRUE
            ORDER BY PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT DESC
            LIMIT :P_LIMIT
        );
    ELSE
        SELECT COUNT(*) INTO :alert_count
        FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_SKU_PRICING_INTELLIGENCE
        WHERE REQUIRES_IMMEDIATE_PRICE_REVIEW = TRUE
          AND CATEGORY = :P_CATEGORY;

        LET rs RESULTSET := (
            SELECT
                SKU_ID, PRODUCT_NAME, CATEGORY, BRAND, OUR_CURRENT_PRICE,
                PRIMARY_COMPETITOR_NAME, PRIMARY_COMPETITOR_PRICE,
                PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT AS PRICE_GAP_PCT,
                STOCK_AVAILABILITY_STATUS AS STOCK_STATUS,
                CORTEX_AI_RECOMMENDATION_SUMMARY AS AI_RECOMMENDATION,
                CORTEX_AI_RECOMMENDED_ACTION_TYPE AS AI_ACTION_TYPE
            FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_SKU_PRICING_INTELLIGENCE
            WHERE REQUIRES_IMMEDIATE_PRICE_REVIEW = TRUE
              AND CATEGORY = :P_CATEGORY
            ORDER BY PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT DESC
            LIMIT :P_LIMIT
        );
    END IF;

    SELECT ARRAY_AGG(OBJECT_CONSTRUCT(
        'sku_id', SKU_ID, 'product_name', PRODUCT_NAME, 'category', CATEGORY,
        'brand', BRAND, 'our_price', OUR_CURRENT_PRICE,
        'competitor_name', PRIMARY_COMPETITOR_NAME, 'competitor_price', PRIMARY_COMPETITOR_PRICE,
        'price_gap_pct', PRICE_GAP_PCT, 'stock_status', STOCK_STATUS,
        'ai_recommendation', AI_RECOMMENDATION, 'ai_action_type', AI_ACTION_TYPE
    ))::VARCHAR INTO :result
    FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));

    RETURN '{"total_alerts": ' || :alert_count || ', "alerts": ' || COALESCE(:result, '[]') || '}';
END;
$$;
