
  
    

        create or replace transient table DEMO_DEV.FRAUD_INTELLIGENCE.SLV_RULE_CODE_KNOWLEDGE_MAP
         as
        (

SELECT
    RULE_CODE,
    RULE_NAME,
    RULE_DESCRIPTION AS DESCRIPTION,
    RULE_CATEGORY AS CATEGORY,
    RISK_WEIGHT,
    IS_ACTIVE,
    CREATED_DATE,
    INGESTED_AT AS LOADED_AT
FROM DEMO_DEV.FRAUD_INTELLIGENCE.stg_raw_rule_definitions
        );
      
  