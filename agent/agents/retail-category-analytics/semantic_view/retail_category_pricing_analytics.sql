-- ============================================================
-- Semantic View: RETAIL_CATEGORY_PRICING_ANALYTICS
-- Schema: DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT
-- Used by: RETAIL_CATEGORY_ANALYTICS_AGENT (cortex_analyst_text_to_sql tool)
-- ============================================================

CREATE OR REPLACE SEMANTIC VIEW RETAIL_CATEGORY_PRICING_ANALYTICS
    TABLES (
        DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.PRICING_INTELLIGENCE_ANALYTICS_VIEW
            COMMENT = 'One row per active SKU with current price, margin, competitor prices, stock status, and AI recommendations.',
        DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.CATEGORY_PERFORMANCE_ANALYTICS_VIEW
            PRIMARY KEY (CATEGORY, FEED_RUN_ID)
            COMMENT = 'One row per category with aggregated KPIs including overpriced counts, margins, and stock metrics.',
        DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.PROMOTION_PERFORMANCE_ANALYTICS_VIEW
            PRIMARY KEY (PROMOTION_ID)
            COMMENT = 'One row per promotion campaign with name, ROAS, unit lift, budget, and performance status (OVER_PERFORMING, ON_TRACK, UNDER_PERFORMING).',
        DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.LOYALTY_CUSTOMER_ANALYTICS_VIEW
            PRIMARY KEY (MEMBER_ID)
            COMMENT = 'One row per loyalty member with name, tier, LTV, churn risk level, customer segment, and spend.',
        DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.RETURNS_MARGIN_ANALYTICS_VIEW
            PRIMARY KEY (SKU_ID)
            COMMENT = 'One row per SKU showing total returns, return rate, margin lost, top return reason, and rationalization flag.'
    )
    FACTS (
        PRICING_INTELLIGENCE_ANALYTICS_VIEW.OUR_CURRENT_PRICE AS OUR_CURRENT_PRICE
            COMMENT = 'Our current selling price in USD',
        PRICING_INTELLIGENCE_ANALYTICS_VIEW.OUR_MARGIN_PERCENTAGE AS OUR_MARGIN_PERCENTAGE
            COMMENT = 'Margin percentage',
        PRICING_INTELLIGENCE_ANALYTICS_VIEW.PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT AS PRICE_GAP_VS_PRIMARY_COMPETITOR_PCT
            COMMENT = 'Price gap vs primary competitor in percent. Positive means we are more expensive.',
        PROMOTION_PERFORMANCE_ANALYTICS_VIEW.ESTIMATED_ROAS AS ESTIMATED_ROAS
            COMMENT = 'Return on Ad Spend for the promotion campaign. Higher is better.',
        PROMOTION_PERFORMANCE_ANALYTICS_VIEW.ACTUAL_UNIT_LIFT_PCT AS ACTUAL_UNIT_LIFT_PCT
            COMMENT = 'Actual unit sales lift percentage achieved during the promotion vs baseline.',
        PROMOTION_PERFORMANCE_ANALYTICS_VIEW.BUDGET_USD AS BUDGET_USD
            COMMENT = 'Marketing budget spent on this promotion in USD.',
        LOYALTY_CUSTOMER_ANALYTICS_VIEW.ESTIMATED_LTV_USD AS ESTIMATED_LTV_USD
            COMMENT = 'Estimated customer lifetime value in USD.',
        LOYALTY_CUSTOMER_ANALYTICS_VIEW.TOTAL_SPEND_USD AS TOTAL_SPEND_USD
            COMMENT = 'Total amount spent by this loyalty member in USD.',
        LOYALTY_CUSTOMER_ANALYTICS_VIEW.CHURN_RISK_SCORE AS CHURN_RISK_SCORE
            COMMENT = 'Churn probability score from 0 to 1. Higher means more likely to churn.',
        RETURNS_MARGIN_ANALYTICS_VIEW.TOTAL_RETURNS AS TOTAL_RETURNS
            COMMENT = 'Total number of product returns for this SKU.',
        RETURNS_MARGIN_ANALYTICS_VIEW.RETURN_RATE_PCT AS RETURN_RATE_PCT
            COMMENT = 'Return rate as percentage of total units sold.',
        RETURNS_MARGIN_ANALYTICS_VIEW.TOTAL_MARGIN_LOST_USD AS TOTAL_MARGIN_LOST_USD
            COMMENT = 'Total margin lost due to returns in USD.'
    )
    DIMENSIONS (
        PRICING_INTELLIGENCE_ANALYTICS_VIEW.SKU_ID AS SKU_ID
            COMMENT = 'Unique SKU identifier e.g. ELEC-SKU-0022',
        PRICING_INTELLIGENCE_ANALYTICS_VIEW.PRODUCT_NAME AS PRODUCT_NAME
            COMMENT = 'Human-readable product name',
        PRICING_INTELLIGENCE_ANALYTICS_VIEW.CATEGORY AS CATEGORY
            COMMENT = 'Product category: GAMING, SMARTPHONES, HOME_THEATER, LAPTOPS, AUDIO',
        PRICING_INTELLIGENCE_ANALYTICS_VIEW.BRAND AS BRAND
            COMMENT = 'Brand or manufacturer name',
        PRICING_INTELLIGENCE_ANALYTICS_VIEW.OVERALL_COMPETITIVE_POSITIONING_STATUS AS OVERALL_COMPETITIVE_POSITIONING_STATUS
            COMMENT = 'Pricing position vs competitors: OVERPRICED, UNDERPRICED, or PRICE_PARITY',
        PROMOTION_PERFORMANCE_ANALYTICS_VIEW.PROMOTION_NAME AS PROMOTION_NAME
            COMMENT = 'Name of the promotion campaign e.g. Fall Audio Kickoff, Gaming Week',
        PROMOTION_PERFORMANCE_ANALYTICS_VIEW.PERFORMANCE_STATUS AS PERFORMANCE_STATUS
            COMMENT = 'Campaign performance classification: OVER_PERFORMING, ON_TRACK, or UNDER_PERFORMING. Use this to find under-performing or over-performing promotions.',
        PROMOTION_PERFORMANCE_ANALYTICS_VIEW.TARGET_CATEGORY AS TARGET_CATEGORY
            COMMENT = 'The product category this promotion targets',
        LOYALTY_CUSTOMER_ANALYTICS_VIEW.FULL_NAME AS FULL_NAME
            COMMENT = 'Customer full name',
        LOYALTY_CUSTOMER_ANALYTICS_VIEW.TIER AS TIER
            COMMENT = 'Loyalty tier: PLATINUM, GOLD, SILVER, or STANDARD',
        LOYALTY_CUSTOMER_ANALYTICS_VIEW.CUSTOMER_SEGMENT AS CUSTOMER_SEGMENT
            COMMENT = 'Customer segment: VIP, LOYAL, AT_RISK, NEW, or DORMANT',
        LOYALTY_CUSTOMER_ANALYTICS_VIEW.CHURN_RISK_LEVEL AS CHURN_RISK_LEVEL
            COMMENT = 'Churn risk level: HIGH, MEDIUM, or LOW. Use this to find at-risk customers.',
        RETURNS_MARGIN_ANALYTICS_VIEW.TOP_RETURN_REASON AS TOP_RETURN_REASON
            COMMENT = 'Most common reason for returns: DEFECTIVE, WRONG_SIZE, NOT_AS_DESCRIBED, CHANGED_MIND',
        RETURNS_MARGIN_ANALYTICS_VIEW.RATIONALIZATION_FLAG AS RATIONALIZATION_FLAG
            COMMENT = 'TRUE if SKU should be considered for removal from assortment due to high returns.'
    )
    COMMENT = 'Retail category analytics covering SKU pricing, promotion campaigns, customer loyalty, and returns. Use PROMOTION_PERFORMANCE_ANALYTICS_VIEW for campaign/ROAS questions. Use LOYALTY_CUSTOMER_ANALYTICS_VIEW for customer/churn questions. Use RETURNS_MARGIN_ANALYTICS_VIEW for return rate questions.'
    AI_VERIFIED_QUERIES (
        UNDER_PERFORMING_PROMOTIONS AS (
            QUESTION 'Which promotions are under-performing?'
            VERIFIED_AT 1747750000
            VERIFIED_BY 'Admin'
            SQL 'SELECT PROMOTION_NAME, TARGET_CATEGORY, ACTUAL_UNIT_LIFT_PCT, ESTIMATED_ROAS, PERFORMANCE_STATUS FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.PROMOTION_PERFORMANCE_ANALYTICS_VIEW WHERE PERFORMANCE_STATUS = ''UNDER_PERFORMING'' ORDER BY ACTUAL_UNIT_LIFT_PCT ASC'
        ),
        BEST_CAMPAIGN_ROAS AS (
            QUESTION 'What is the ROAS of the best performing campaign?'
            VERIFIED_AT 1747750000
            VERIFIED_BY 'Admin'
            SQL 'SELECT PROMOTION_NAME, ESTIMATED_ROAS, ACTUAL_UNIT_LIFT_PCT, BUDGET_USD, PERFORMANCE_STATUS FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.PROMOTION_PERFORMANCE_ANALYTICS_VIEW ORDER BY ESTIMATED_ROAS DESC LIMIT 1'
        ),
        HIGH_CHURN_CUSTOMERS AS (
            QUESTION 'Which customers are at high churn risk?'
            VERIFIED_AT 1747750000
            VERIFIED_BY 'Admin'
            SQL 'SELECT FULL_NAME, TIER, CUSTOMER_SEGMENT, CHURN_RISK_LEVEL, ESTIMATED_LTV_USD, TOTAL_SPEND_USD FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.LOYALTY_CUSTOMER_ANALYTICS_VIEW WHERE CHURN_RISK_LEVEL = ''HIGH'' ORDER BY ESTIMATED_LTV_USD DESC'
        ),
        HIGHEST_RETURN_RATES AS (
            QUESTION 'Which SKUs have the highest return rates?'
            VERIFIED_AT 1747750000
            VERIFIED_BY 'Admin'
            SQL 'SELECT PRODUCT_NAME, CATEGORY, TOTAL_RETURNS, RETURN_RATE_PCT, TOTAL_MARGIN_LOST_USD, TOP_RETURN_REASON FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.RETURNS_MARGIN_ANALYTICS_VIEW ORDER BY RETURN_RATE_PCT DESC LIMIT 10'
        )
    );
