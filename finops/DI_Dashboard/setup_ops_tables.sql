------------------------------------------------------------------------
-- ADMIN_DB.OPS  –  FinOps Dashboard Pre-Computed Tables + Semantic View
-- Run once with SYSADMIN on ADMIN_WH, then CALL SP_REFRESH_DASHBOARD_TABLES()
------------------------------------------------------------------------

USE ROLE SYSADMIN;
USE WAREHOUSE ADMIN_WH;

CREATE DATABASE IF NOT EXISTS ADMIN_DB;
CREATE SCHEMA IF NOT EXISTS ADMIN_DB.OPS;

------------------------------------------------------------------------
-- 1. OPS TABLES (pre-computed summaries)
------------------------------------------------------------------------

CREATE OR REPLACE TABLE ADMIN_DB.OPS.OPS_DATA_MODALITY (
    DATA_MODALITY    VARCHAR(200),
    COLUMN_COUNT     NUMBER,
    TABLE_COUNT      NUMBER,
    REFRESHED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE ADMIN_DB.OPS.OPS_VARIANT_RICHNESS (
    VARIANT_COLUMN   VARCHAR(500),
    STRUCTURE_TYPE   VARCHAR(100),
    ROW_COUNT        NUMBER,
    UNIQUE_KEYS      NUMBER,
    REFRESHED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE ADMIN_DB.OPS.OPS_DQ_AUDIT_SUMMARY (
    TABLE_NAME       VARCHAR(500),
    CHECK_TYPE       VARCHAR(200),
    CHECK_COUNT      NUMBER,
    UNIQUE_SOURCES   NUMBER,
    COLUMNS_FLAGGED  NUMBER,
    LATEST_AUDIT     TIMESTAMP_NTZ,
    REFRESHED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE ADMIN_DB.OPS.OPS_ML_EVALUATION (
    MODEL_NAME       VARCHAR(500),
    VERSION_NAME     VARCHAR(200),
    ALGORITHM        VARCHAR(200),
    AUC              FLOAT,
    ACCURACY         FLOAT,
    PRECISION_SCORE  FLOAT,
    RECALL_SCORE     FLOAT,
    F1_SCORE         FLOAT,
    TRAIN_ROW_COUNT  NUMBER,
    TEST_ROW_COUNT   NUMBER,
    RUN_AT           TIMESTAMP_NTZ,
    REFRESHED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE ADMIN_DB.OPS.OPS_ML_INFERENCE (
    MODEL_NAME       VARCHAR(500),
    VERSION_NAME     VARCHAR(200),
    SP_NAME          VARCHAR(500),
    PATIENT_COUNT    NUMBER,
    EXECUTION_TIME_MS NUMBER,
    STATUS           VARCHAR(50),
    ERROR_MESSAGE    VARCHAR(2000),
    RUN_AT           TIMESTAMP_NTZ,
    RUN_BY           VARCHAR(200),
    REFRESHED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE ADMIN_DB.OPS.OPS_AGENT_COST (
    AGENT_NAME          VARCHAR(500),
    RUNS                NUMBER,
    TOTAL_TOKENS        NUMBER,
    TOTAL_CREDITS       FLOAT,
    AVG_TOKENS_PER_RUN  NUMBER,
    AVG_CREDITS_PER_RUN FLOAT,
    REFRESHED_AT        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE ADMIN_DB.OPS.OPS_AI_FUNCTION_USAGE (
    FUNCTION_NAME    VARCHAR(200),
    MODEL_NAME       VARCHAR(200),
    CALL_COUNT       NUMBER,
    TOTAL_CREDITS    FLOAT,
    REFRESHED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE TABLE ADMIN_DB.OPS.OPS_DAILY_AI_SPEND (
    DAY              DATE,
    AGENT_RUNS       NUMBER,
    DAILY_TOKENS     NUMBER,
    DAILY_CREDITS    FLOAT,
    REFRESHED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

------------------------------------------------------------------------
-- 2. STORED PROCEDURE – Refreshes all OPS tables
------------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE ADMIN_DB.OPS.SP_REFRESH_DASHBOARD_TABLES()
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
BEGIN
    -- Data Modality
    TRUNCATE TABLE ADMIN_DB.OPS.OPS_DATA_MODALITY;
    INSERT INTO ADMIN_DB.OPS.OPS_DATA_MODALITY (DATA_MODALITY, COLUMN_COUNT, TABLE_COUNT)
    SELECT
        CASE
            WHEN DATA_TYPE = 'VARIANT' THEN 'Semi-Structured (JSON)'
            WHEN DATA_TYPE IN ('TEXT', 'VARCHAR') AND TABLE_NAME IN ('VBC_AI_INSIGHTS', 'GOLD_CARE_PLANS', 'GOLD_CARE_MANAGEMENT_RECOMMENDATIONS') THEN 'AI-Generated Text'
            WHEN DATA_TYPE IN ('TEXT', 'VARCHAR') THEN 'Structured Text'
            WHEN DATA_TYPE IN ('NUMBER', 'FIXED') AND TABLE_NAME LIKE 'ML_%' THEN 'ML Features'
            WHEN DATA_TYPE = 'FLOAT' AND TABLE_NAME LIKE 'ML_%' THEN 'ML Features'
            WHEN DATA_TYPE IN ('NUMBER', 'FIXED', 'FLOAT') THEN 'Structured Numeric'
            WHEN DATA_TYPE IN ('TIMESTAMP_NTZ', 'TIMESTAMP_LTZ', 'TIMESTAMP_TZ', 'DATE') THEN 'Temporal'
            WHEN DATA_TYPE = 'BOOLEAN' THEN 'Boolean Flags'
            ELSE DATA_TYPE
        END,
        COUNT(*),
        COUNT(DISTINCT TABLE_NAME)
    FROM DEMO_DEV.INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA')
    GROUP BY 1
    ORDER BY 2 DESC;

    -- Variant Richness
    TRUNCATE TABLE ADMIN_DB.OPS.OPS_VARIANT_RICHNESS;
    INSERT INTO ADMIN_DB.OPS.OPS_VARIANT_RICHNESS (VARIANT_COLUMN, STRUCTURE_TYPE, ROW_COUNT, UNIQUE_KEYS)
    SELECT 'VBC_FINANCIAL_DATA.VARIANCE_DATA', 'JSON Object',
           (SELECT COUNT(*) FROM DEMO_DEV.VALUE_BASED_CARE.VBC_FINANCIAL_DATA),
           (SELECT COUNT(DISTINCT f.key) FROM DEMO_DEV.VALUE_BASED_CARE.VBC_FINANCIAL_DATA, LATERAL FLATTEN(input => VARIANCE_DATA) f);
    INSERT INTO ADMIN_DB.OPS.OPS_VARIANT_RICHNESS (VARIANT_COLUMN, STRUCTURE_TYPE, ROW_COUNT, UNIQUE_KEYS)
    SELECT 'VBC_FINANCIAL_DATA.DENIAL_REASON_DATA', 'JSON Array',
           (SELECT COUNT(*) FROM DEMO_DEV.VALUE_BASED_CARE.VBC_FINANCIAL_DATA WHERE DENIAL_REASON_DATA IS NOT NULL),
           (SELECT COUNT(DISTINCT f.value:reason::STRING) FROM DEMO_DEV.VALUE_BASED_CARE.VBC_FINANCIAL_DATA, LATERAL FLATTEN(input => DENIAL_REASON_DATA) f);

    -- DQ Audit
    TRUNCATE TABLE ADMIN_DB.OPS.OPS_DQ_AUDIT_SUMMARY;
    INSERT INTO ADMIN_DB.OPS.OPS_DQ_AUDIT_SUMMARY (TABLE_NAME, CHECK_TYPE, CHECK_COUNT, UNIQUE_SOURCES, COLUMNS_FLAGGED, LATEST_AUDIT)
    SELECT TABLE_NAME, CHECK_TYPE, COUNT(*), COUNT(DISTINCT SOURCE_ID), COUNT(FAILED_COLUMN), MAX(AUDIT_TS)
    FROM DEMO_DEV.VALUE_BASED_CARE.SILVER_DQ_AUDIT_LOG
    GROUP BY 1, 2
    ORDER BY 3 DESC;

    -- ML Evaluation
    TRUNCATE TABLE ADMIN_DB.OPS.OPS_ML_EVALUATION;
    INSERT INTO ADMIN_DB.OPS.OPS_ML_EVALUATION (MODEL_NAME, VERSION_NAME, ALGORITHM, AUC, ACCURACY, PRECISION_SCORE, RECALL_SCORE, F1_SCORE, TRAIN_ROW_COUNT, TEST_ROW_COUNT, RUN_AT)
    SELECT MODEL_NAME, VERSION_NAME, ALGORITHM, ROUND(AUC,4), ROUND(ACCURACY,4), ROUND(PRECISION_SCORE,4), ROUND(RECALL_SCORE,4), ROUND(F1_SCORE,4), TRAIN_ROW_COUNT, TEST_ROW_COUNT, RUN_AT
    FROM DEMO_DEV.VALUE_BASED_CARE.ML_MODEL_EVALUATION_LOG
    ORDER BY RUN_AT DESC
    LIMIT 100;

    -- ML Inference
    TRUNCATE TABLE ADMIN_DB.OPS.OPS_ML_INFERENCE;
    INSERT INTO ADMIN_DB.OPS.OPS_ML_INFERENCE (MODEL_NAME, VERSION_NAME, SP_NAME, PATIENT_COUNT, EXECUTION_TIME_MS, STATUS, ERROR_MESSAGE, RUN_AT, RUN_BY)
    SELECT MODEL_NAME, VERSION_NAME, SP_NAME, PATIENT_COUNT, EXECUTION_TIME_MS, STATUS, ERROR_MESSAGE, RUN_AT, RUN_BY
    FROM DEMO_DEV.VALUE_BASED_CARE.ML_MODEL_INFERENCE_LOG
    ORDER BY RUN_AT DESC
    LIMIT 100;

    -- Agent Cost
    TRUNCATE TABLE ADMIN_DB.OPS.OPS_AGENT_COST;
    INSERT INTO ADMIN_DB.OPS.OPS_AGENT_COST (AGENT_NAME, RUNS, TOTAL_TOKENS, TOTAL_CREDITS, AVG_TOKENS_PER_RUN, AVG_CREDITS_PER_RUN)
    SELECT AGENT_NAME, COUNT(*), SUM(TOKENS), ROUND(SUM(TOKEN_CREDITS),6), ROUND(AVG(TOKENS),0), ROUND(AVG(TOKEN_CREDITS),6)
    FROM ACCOUNT_USAGE_SECURE.USAGE.CORTEX_AGENT_USAGE_HISTORY
    WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP()) AND AGENT_NAME IS NOT NULL
    GROUP BY 1
    ORDER BY 4 DESC;

    -- AI Function Usage
    TRUNCATE TABLE ADMIN_DB.OPS.OPS_AI_FUNCTION_USAGE;
    INSERT INTO ADMIN_DB.OPS.OPS_AI_FUNCTION_USAGE (FUNCTION_NAME, MODEL_NAME, CALL_COUNT, TOTAL_CREDITS)
    SELECT FUNCTION_NAME, MODEL_NAME, COUNT(*), ROUND(SUM(CREDITS),6)
    FROM ACCOUNT_USAGE_SECURE.USAGE.CORTEX_AI_FUNCTIONS_USAGE_HISTORY
    WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
    GROUP BY 1, 2
    ORDER BY 4 DESC;

    -- Daily AI Spend
    TRUNCATE TABLE ADMIN_DB.OPS.OPS_DAILY_AI_SPEND;
    INSERT INTO ADMIN_DB.OPS.OPS_DAILY_AI_SPEND (DAY, AGENT_RUNS, DAILY_TOKENS, DAILY_CREDITS)
    SELECT DATE_TRUNC('day', START_TIME), COUNT(*), SUM(TOKENS), ROUND(SUM(TOKEN_CREDITS),6)
    FROM ACCOUNT_USAGE_SECURE.USAGE.CORTEX_AGENT_USAGE_HISTORY
    WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
    GROUP BY 1
    ORDER BY 1;

    RETURN 'All OPS tables refreshed successfully at ' || CURRENT_TIMESTAMP()::STRING;
END;
$$;

------------------------------------------------------------------------
-- 3. SEMANTIC VIEW – FinOps Advisor (via SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML)
------------------------------------------------------------------------

CALL SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML(
  'ADMIN_DB.OPS',
  $$
  name: FINOPS_ADVISOR
  description: "FinOps intelligence semantic view over DEMO_DEV data architecture, data quality, ML operations, and AI credit economics"

  tables:
    - name: AGENT_COST
      description: "Cortex Agent token and credit spend summary (last 30 days)"
      base_table:
        database: ADMIN_DB
        schema: OPS
        table: OPS_AGENT_COST
      dimensions:
        - name: AGENT_NAME
          synonyms:
            - agent
            - cortex agent
          description: "Name of the Cortex Agent"
          expr: AGENT_NAME
          data_type: VARCHAR(500)
      metrics:
        - name: TOTAL_AGENT_RUNS
          description: "Total number of agent invocations"
          expr: SUM(RUNS)
        - name: TOTAL_TOKENS_CONSUMED
          synonyms:
            - token usage
            - total tokens
          description: "Total tokens consumed across all agents"
          expr: SUM(TOTAL_TOKENS)
        - name: TOTAL_AGENT_CREDITS
          synonyms:
            - agent cost
            - agent spend
            - credit spend
          description: "Total credits spent on agent runs"
          expr: SUM(TOTAL_CREDITS)
        - name: AVG_TOKENS_PER_AGENT_RUN
          description: "Average tokens per agent invocation"
          expr: AVG(AVG_TOKENS_PER_RUN)

    - name: AI_FUNCTION_USAGE
      description: "Cortex AI function usage and credit spend by model (last 30 days)"
      base_table:
        database: ADMIN_DB
        schema: OPS
        table: OPS_AI_FUNCTION_USAGE
      dimensions:
        - name: FUNCTION_NAME
          synonyms:
            - AI function
            - cortex function
          description: "Name of the Cortex AI function (e.g. COMPLETE, SUMMARIZE, EXTRACT)"
          expr: FUNCTION_NAME
          data_type: VARCHAR(200)
        - name: AI_MODEL_NAME
          synonyms:
            - model
            - LLM model
          description: "LLM model used by the function"
          expr: MODEL_NAME
          data_type: VARCHAR(200)
      metrics:
        - name: TOTAL_FUNCTION_CALLS
          description: "Total number of AI function calls"
          expr: SUM(CALL_COUNT)
        - name: TOTAL_FUNCTION_CREDITS
          synonyms:
            - function cost
            - function spend
          description: "Total credits spent on AI function calls"
          expr: SUM(TOTAL_CREDITS)

    - name: DAILY_AI_SPEND
      description: "Daily aggregated AI credit spend trend (last 30 days)"
      base_table:
        database: ADMIN_DB
        schema: OPS
        table: OPS_DAILY_AI_SPEND
      time_dimensions:
        - name: SPEND_DATE
          synonyms:
            - day
            - date
          description: "Date of AI spend"
          expr: DAY
          data_type: DATE
      metrics:
        - name: DAILY_AGENT_RUNS
          description: "Number of agent runs on a given day"
          expr: SUM(AGENT_RUNS)
        - name: DAILY_TOKEN_USAGE
          description: "Total tokens consumed on a given day"
          expr: SUM(DAILY_TOKENS)
        - name: DAILY_CREDIT_SPEND
          synonyms:
            - daily cost
            - daily credits
          description: "Total credits spent on AI on a given day"
          expr: SUM(DAILY_CREDITS)

    - name: DATA_MODALITY
      description: "Data modality distribution across all schemas in DEMO_DEV"
      base_table:
        database: ADMIN_DB
        schema: OPS
        table: OPS_DATA_MODALITY
      dimensions:
        - name: MODALITY_TYPE
          synonyms:
            - data type
            - column type
            - modality
          description: "Category of data modality (e.g. Structured Numeric, AI-Generated Text, Semi-Structured JSON)"
          expr: DATA_MODALITY
          data_type: VARCHAR(200)
      metrics:
        - name: MODALITY_COLUMN_COUNT
          description: "Number of columns of this modality type"
          expr: SUM(COLUMN_COUNT)
        - name: MODALITY_TABLE_COUNT
          description: "Number of tables containing this modality type"
          expr: SUM(TABLE_COUNT)

    - name: DQ_AUDIT
      description: "Data quality audit summary from DEMO_DEV silver layer"
      base_table:
        database: ADMIN_DB
        schema: OPS
        table: OPS_DQ_AUDIT_SUMMARY
      dimensions:
        - name: DQ_TABLE_NAME
          synonyms:
            - table
            - audited table
          description: "Name of the table that was audited"
          expr: TABLE_NAME
          data_type: VARCHAR(500)
        - name: DQ_CHECK_TYPE
          synonyms:
            - check type
            - validation type
          description: "Type of data quality check performed"
          expr: CHECK_TYPE
          data_type: VARCHAR(200)
      time_dimensions:
        - name: DQ_LATEST_AUDIT
          description: "Most recent audit timestamp for this check"
          expr: LATEST_AUDIT
          data_type: TIMESTAMP_NTZ
      metrics:
        - name: TOTAL_DQ_CHECKS
          synonyms:
            - quality checks
            - audit count
          description: "Total number of DQ checks performed"
          expr: SUM(CHECK_COUNT)
        - name: TOTAL_COLUMNS_FLAGGED
          synonyms:
            - flagged columns
            - quality issues
          description: "Total columns flagged with quality issues"
          expr: SUM(COLUMNS_FLAGGED)

    - name: ML_EVALUATION
      description: "ML model evaluation metrics from DEMO_DEV"
      base_table:
        database: ADMIN_DB
        schema: OPS
        table: OPS_ML_EVALUATION
      dimensions:
        - name: ML_MODEL_NAME
          synonyms:
            - model name
            - ML model
          description: "Name of the trained ML model"
          expr: MODEL_NAME
          data_type: VARCHAR(500)
        - name: ML_VERSION
          synonyms:
            - version
            - model version
          description: "Version of the model"
          expr: VERSION_NAME
          data_type: VARCHAR(200)
        - name: ML_ALGORITHM
          synonyms:
            - algorithm
          description: "Algorithm used for training"
          expr: ALGORITHM
          data_type: VARCHAR(200)
      time_dimensions:
        - name: ML_EVAL_DATE
          description: "Date of model evaluation run"
          expr: RUN_AT
          data_type: TIMESTAMP_NTZ
      metrics:
        - name: AVG_AUC
          description: "Average AUC score across model evaluations"
          expr: AVG(AUC)
        - name: AVG_ACCURACY
          description: "Average accuracy score"
          expr: AVG(ACCURACY)
        - name: AVG_F1
          description: "Average F1 score"
          expr: AVG(F1_SCORE)

    - name: ML_INFERENCE
      description: "ML model inference run history from DEMO_DEV"
      base_table:
        database: ADMIN_DB
        schema: OPS
        table: OPS_ML_INFERENCE
      dimensions:
        - name: INFERENCE_MODEL
          description: "Model used for inference"
          expr: MODEL_NAME
          data_type: VARCHAR(500)
        - name: INFERENCE_STATUS
          synonyms:
            - status
            - run status
          description: "Status of inference run (SUCCESS/FAILED)"
          expr: STATUS
          data_type: VARCHAR(50)
      time_dimensions:
        - name: INFERENCE_DATE
          description: "Date of inference run"
          expr: RUN_AT
          data_type: TIMESTAMP_NTZ
      metrics:
        - name: TOTAL_INFERENCE_RUNS
          description: "Total number of inference runs"
          expr: COUNT(*)
        - name: AVG_EXECUTION_TIME_MS
          synonyms:
            - avg runtime
            - execution time
          description: "Average execution time in milliseconds (proxy for compute cost)"
          expr: AVG(EXECUTION_TIME_MS)
        - name: TOTAL_PATIENTS_SCORED
          description: "Total patients scored across inference runs"
          expr: SUM(PATIENT_COUNT)

  verified_queries:
    - name: most_expensive_agent
      question: "Which agent costs the most credits?"
      sql: "SELECT AGENT_NAME, TOTAL_CREDITS FROM ADMIN_DB.OPS.OPS_AGENT_COST ORDER BY TOTAL_CREDITS DESC LIMIT 5"
      use_as_onboarding_question: true
    - name: total_ai_spend
      question: "What is the total AI credit spend?"
      sql: "SELECT SUM(TOTAL_CREDITS) AS TOTAL_AI_CREDITS FROM ADMIN_DB.OPS.OPS_AGENT_COST"
      use_as_onboarding_question: true
    - name: data_modalities
      question: "What data types exist in DEMO_DEV?"
      sql: "SELECT DATA_MODALITY, COLUMN_COUNT, TABLE_COUNT FROM ADMIN_DB.OPS.OPS_DATA_MODALITY ORDER BY COLUMN_COUNT DESC"
      use_as_onboarding_question: true
    - name: daily_spend_trend
      question: "Show me the daily AI credit spend trend"
      sql: "SELECT DAY, DAILY_CREDITS FROM ADMIN_DB.OPS.OPS_DAILY_AI_SPEND ORDER BY DAY"
    - name: dq_issues
      question: "Which tables have the most data quality issues?"
      sql: "SELECT TABLE_NAME, SUM(COLUMNS_FLAGGED) AS TOTAL_FLAGS FROM ADMIN_DB.OPS.OPS_DQ_AUDIT_SUMMARY GROUP BY 1 ORDER BY 2 DESC LIMIT 10"
    - name: model_performance
      question: "What is the latest model accuracy?"
      sql: "SELECT MODEL_NAME, VERSION_NAME, ACCURACY, AUC, F1_SCORE FROM ADMIN_DB.OPS.OPS_ML_EVALUATION ORDER BY RUN_AT DESC LIMIT 1"
    - name: inference_failures
      question: "Are there any failed inference runs?"
      sql: "SELECT MODEL_NAME, STATUS, ERROR_MESSAGE, RUN_AT FROM ADMIN_DB.OPS.OPS_ML_INFERENCE WHERE STATUS != 'SUCCESS' ORDER BY RUN_AT DESC"
    - name: cheapest_model
      question: "Which AI model is cheapest?"
      sql: "SELECT MODEL_NAME, SUM(TOTAL_CREDITS) AS CREDITS FROM ADMIN_DB.OPS.OPS_AI_FUNCTION_USAGE GROUP BY 1 ORDER BY 2 ASC LIMIT 5"
    - name: most_used_function
      question: "Which AI function is called the most?"
      sql: "SELECT FUNCTION_NAME, SUM(CALL_COUNT) AS CALLS FROM ADMIN_DB.OPS.OPS_AI_FUNCTION_USAGE GROUP BY 1 ORDER BY 2 DESC LIMIT 5"
  $$
);

------------------------------------------------------------------------
-- 4. GRANT PRIVILEGES
------------------------------------------------------------------------

GRANT USAGE ON DATABASE ADMIN_DB TO ROLE SYSADMIN;
GRANT USAGE ON SCHEMA ADMIN_DB.OPS TO ROLE SYSADMIN;
GRANT SELECT ON ALL TABLES IN SCHEMA ADMIN_DB.OPS TO ROLE SYSADMIN;
GRANT REFERENCES, SELECT ON SEMANTIC VIEW ADMIN_DB.OPS.FINOPS_ADVISOR TO ROLE SYSADMIN;

------------------------------------------------------------------------
-- 5. INITIAL LOAD
------------------------------------------------------------------------

CALL ADMIN_DB.OPS.SP_REFRESH_DASHBOARD_TABLES();
