USE ROLE AGENT_DEMO_ROLE;
USE WAREHOUSE AGENT_DEMO_WH;
USE SCHEMA DEMO_DEV.FRAUD_INTELLIGENCE;

CREATE OR REPLACE NOTEBOOK PROJECT DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_TRAINING_NOTEBOOK_PROJECT
    FROM 'snow://workspace/USER$.PUBLIC.DEFAULT$/versions/live'
    COMMENT = 'Fraud Detection Model training notebook — XGBClassifier trained on GLD_ML_TRAINING_SET with agent-labelled fraud data. Registers model to ML Registry and logs performance to SLV_MODEL_PERFORMANCE_LOG.';
