
  
    

        create or replace transient table DEMO_DEV.FRAUD_INTELLIGENCE.SLV_INVESTIGATION_KNOWLEDGE_BASE
         as
        (

SELECT
    DOC_ID,
    DOC_TITLE AS TITLE,
    DOC_CONTENT AS CONTENT,
    DOC_CATEGORY AS CATEGORY,
    EFFECTIVE_DATE,
    INGESTED_AT AS LOADED_AT
FROM DEMO_DEV.FRAUD_INTELLIGENCE.stg_raw_investigation_docs
        );
      
  