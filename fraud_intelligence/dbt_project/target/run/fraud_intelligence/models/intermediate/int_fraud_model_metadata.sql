
  
    

        create or replace transient table DEMO_DEV.FRAUD_INTELLIGENCE.SLV_FRAUD_MODEL_METADATA
         as
        (

SELECT
    MODEL_NAME,
    MODEL_VERSION_NAME          AS MODEL_VERSION,
    'XGBClassifier'             AS MODEL_TYPE,
    'ACTIVE'                    AS MODEL_STATUS,
    CREATED_ON                  AS LAST_TRAINED_AT,
    CREATED_ON                  AS CREATED_AT
FROM (
    SELECT
        MODEL_NAME,
        MODEL_VERSION_NAME,
        METADATA:metrics:auc_roc::FLOAT AS AUC_ROC,
        CREATED_ON,
        ROW_NUMBER() OVER (ORDER BY METADATA:metrics:auc_roc::FLOAT DESC NULLS LAST,
                                    CREATED_ON DESC) AS rn
    FROM DEMO_DEV.INFORMATION_SCHEMA.MODEL_VERSIONS
    WHERE MODEL_NAME = 'FRAUD_DETECTION_MODEL'
      AND METADATA:metrics:auc_roc::FLOAT > 0.6
)
WHERE rn = 1
        );
      
  