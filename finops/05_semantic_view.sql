CREATE OR REPLACE SEMANTIC VIEW ADMIN_DB.OPS.FINOPS_VALUE_INTELLIGENCE_SV

  TABLES (
    cost_value_mapping AS ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
      PRIMARY KEY (VALUE_DATE),
    alert_outcomes AS DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED
      PRIMARY KEY (ALERT_ID)
  )

  DIMENSIONS (
    cost_value_mapping.value_date AS VALUE_DATE
      COMMENT = 'Calendar date for daily cost and value metrics',
    cost_value_mapping.warehouse_name AS WAREHOUSE_NAME
      COMMENT = 'Snowflake warehouse name',
    cost_value_mapping.cost_is_simulated AS COST_IS_SIMULATED
      COMMENT = 'Whether cost data is real or simulated',
    alert_outcomes.alert_date AS DATE_TRUNC('DAY', ALERT_DATE)
      COMMENT = 'Alert date truncated to calendar day',
    alert_outcomes.disposition AS DISPOSITION
      COMMENT = 'Analyst disposition of the alert',
    alert_outcomes.ml_risk_tier AS ML_RISK_TIER
      COMMENT = 'ML model risk classification tier',
    alert_outcomes.rule_code AS RULE_CODE
      COMMENT = 'Detection rule that triggered the alert',
    alert_outcomes.analyst_id AS ANALYST_ID
      COMMENT = 'Analyst assigned to review the alert'
  )

  METRICS (
    cost_value_mapping.total_credits AS SUM(TOTAL_CREDITS)
      COMMENT = 'Total compute credits consumed by AGENT_DEMO_WH',
    cost_value_mapping.idle_credits AS SUM(IDLE_CREDITS)
      COMMENT = 'Credits consumed with no query activity',
    cost_value_mapping.productive_credits AS SUM(PRODUCTIVE_CREDITS)
      COMMENT = 'Credits consumed during active query execution',
    cost_value_mapping.alerts_processed AS SUM(ALERTS_PROCESSED)
      COMMENT = 'Total fraud alerts processed on this date',
    cost_value_mapping.confirmed_fraud_count AS SUM(SAR_FILED_COUNT)
      COMMENT = 'Confirmed fraud cases resulting in SAR filing',
    cost_value_mapping.fraud_amount_protected AS SUM(FRAUD_AMOUNT_PROTECTED)
      COMMENT = 'Total transaction value of confirmed fraud detected',
    cost_value_mapping.fraud_amount_per_credit AS AVG(FRAUD_AMOUNT_PER_CREDIT)
      COMMENT = 'Business value delivered per compute credit',
    cost_value_mapping.sar_cost_per_filing AS AVG(SAR_COST_PER_FILING)
      COMMENT = 'Dollar cost of compute per SAR filed at $3 per credit',
    cost_value_mapping.idle_pct AS AVG(IDLE_PCT)
      COMMENT = 'Percentage of compute spent with no active workload',
    alert_outcomes.total_alerts AS COUNT(DISTINCT ALERT_ID)
      COMMENT = 'Total fraud alerts in pipeline',
    alert_outcomes.confirmed_fraud_alerts AS COUNT(DISTINCT CASE WHEN DISPOSITION = 'CONFIRMED_FRAUD' THEN ALERT_ID END)
      COMMENT = 'Analyst-confirmed fraud cases',
    alert_outcomes.pending_alerts AS COUNT(DISTINCT CASE WHEN DISPOSITION IS NULL THEN ALERT_ID END)
      COMMENT = 'Alerts awaiting analyst disposition',
    alert_outcomes.avg_ml_fraud_score AS AVG(ML_FRAUD_SCORE)
      COMMENT = 'Average ML confidence score across alerts',
    alert_outcomes.confirmation_rate AS alert_outcomes.confirmed_fraud_alerts / NULLIF(alert_outcomes.total_alerts, 0)
      COMMENT = 'Ratio of confirmed fraud to total alerts processed'
  )

  COMMENT = 'FinOps semantic view mapping fraud intelligence value to compute cost'

  AI_VERIFIED_QUERIES (
    fraud_value_per_credit_this_month AS (
      QUESTION 'What is my fraud amount protected per credit spent this month?'
      VERIFIED_AT 1748649600
      ONBOARDING_QUESTION TRUE
      VERIFIED_BY '(STEWARD = finops_team)'
      SQL 'SELECT VALUE_DATE, FRAUD_AMOUNT_PROTECTED, TOTAL_CREDITS, FRAUD_AMOUNT_PER_CREDIT FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING WHERE VALUE_DATE >= DATE_TRUNC(''MONTH'', CURRENT_DATE()) ORDER BY VALUE_DATE ASC'
    ),
    sar_filing_cost_this_month AS (
      QUESTION 'How many SARs were filed this month and what did each one cost in compute?'
      VERIFIED_AT 1748649600
      ONBOARDING_QUESTION TRUE
      VERIFIED_BY '(STEWARD = finops_team)'
      SQL 'SELECT SUM(SAR_FILED_COUNT) AS total_sars_filed, SUM(TOTAL_CREDITS) AS total_credits_used, SUM(TOTAL_CREDITS) * 3 / NULLIF(SUM(SAR_FILED_COUNT), 0) AS cost_per_sar FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING WHERE VALUE_DATE >= DATE_TRUNC(''MONTH'', CURRENT_DATE())'
    ),
    pending_alerts_by_rule AS (
      QUESTION 'What percentage of alerts are pending disposition and which rule codes have the most?'
      VERIFIED_AT 1748649600
      ONBOARDING_QUESTION FALSE
      VERIFIED_BY '(STEWARD = finops_team)'
      SQL 'SELECT RULE_CODE, COUNT(DISTINCT ALERT_ID) AS total_alerts, COUNT(DISTINCT CASE WHEN DISPOSITION = ''CONFIRMED_FRAUD'' THEN ALERT_ID END) AS confirmed_fraud_alerts, COUNT(DISTINCT CASE WHEN DISPOSITION IS NULL THEN ALERT_ID END) AS pending_alerts, ROUND(COUNT(DISTINCT CASE WHEN DISPOSITION = ''CONFIRMED_FRAUD'' THEN ALERT_ID END) / NULLIF(COUNT(DISTINCT ALERT_ID), 0) * 100, 1) AS confirmation_pct FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED GROUP BY RULE_CODE ORDER BY pending_alerts DESC LIMIT 10'
    ),
    worst_cost_efficiency_days AS (
      QUESTION 'On my worst cost-efficiency days what happened?'
      VERIFIED_AT 1748649600
      ONBOARDING_QUESTION FALSE
      VERIFIED_BY '(STEWARD = finops_team)'
      SQL 'SELECT VALUE_DATE, IDLE_PCT, ALERTS_PROCESSED, SAR_FILED_COUNT AS confirmed_fraud_count, FRAUD_AMOUNT_PER_CREDIT FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING WHERE ALERTS_PROCESSED > 0 ORDER BY IDLE_PCT DESC LIMIT 5'
    )
  );

/*Valdiation of Semantic ViewSELECT * FROM ADMIN_DB.OPS.FINOPS_VALUE_INTELLIGENCE_SV;
*/
SELECT VALUE_DATE AS value_date, IDLE_CREDITS / NULLIF(TOTAL_CREDITS, 0) * 100 AS idle_pct, ALERTS_PROCESSED AS alerts_processed, SAR_FILED_COUNT AS confirmed_fraud_count, FRAUD_AMOUNT_PER_CREDIT AS fraud_amount_per_credit FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING WHERE ALERTS_PROCESSED > 0 ORDER BY idle_pct DESC LIMIT 5;
SELECT VALUE_DATE AS value_date, FRAUD_AMOUNT_PROTECTED AS fraud_amount_protected, TOTAL_CREDITS AS total_credits, FRAUD_AMOUNT_PER_CREDIT AS fraud_amount_per_credit FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING WHERE VALUE_DATE >= DATE_TRUNC('MONTH', CURRENT_DATE()) ORDER BY VALUE_DATE ASC;
SELECT SUM(SAR_FILED_COUNT) AS total_sars_filed, SUM(TOTAL_CREDITS) AS total_credits_used, SUM(TOTAL_CREDITS) * 3 / NULLIF(SUM(SAR_FILED_COUNT), 0) AS cost_per_sar FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING WHERE VALUE_DATE >= DATE_TRUNC('MONTH', CURRENT_DATE());
SELECT RULE_CODE AS rule_code, COUNT(DISTINCT ALERT_ID) AS total_alerts, COUNT(DISTINCT CASE WHEN DISPOSITION = 'CONFIRMED_FRAUD' THEN ALERT_ID END) AS confirmed_fraud_alerts, COUNT(DISTINCT CASE WHEN DISPOSITION IS NULL THEN ALERT_ID END) AS pending_alerts, ROUND(COUNT(DISTINCT CASE WHEN DISPOSITION = 'CONFIRMED_FRAUD' THEN ALERT_ID END) / NULLIF(COUNT(DISTINCT ALERT_ID), 0) * 100, 1) AS confirmation_pct FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED GROUP BY RULE_CODE ORDER BY pending_alerts DESC LIMIT 10;

SELECT SUM(SAR_FILED_COUNT)
FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
WHERE VALUE_DATE >= DATE_TRUNC('MONTH', CURRENT_DATE());