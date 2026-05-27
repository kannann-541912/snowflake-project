USE ROLE ACCOUNTADMIN;

-- 1. Create dedicated inference compute pool (isolated from Streamlit/ETL)
CREATE COMPUTE POOL IF NOT EXISTS FRAUD_INFERENCE_POOL
    MIN_NODES = 1
    MAX_NODES = 1
    INSTANCE_FAMILY = CPU_X64_XS
    AUTO_SUSPEND_SECS = 300
    AUTO_RESUME = TRUE
    COMMENT = 'Dedicated ML inference pool for fraud scoring — isolated from Streamlit and ETL workloads';

-- 2. Grant privileges
GRANT USAGE ON COMPUTE POOL FRAUD_INFERENCE_POOL TO ROLE AGENT_DEMO_ROLE;
GRANT BIND SERVICE ENDPOINT ON ACCOUNT TO ROLE AGENT_DEMO_ROLE;
GRANT CREATE GATEWAY ON SCHEMA DEMO_DEV.FRAUD_INTELLIGENCE TO ROLE AGENT_DEMO_ROLE;

-- 3. Deploy V1 (champion) as inference service
-- Run from Python (notebook cell 3):
--   reg = Registry(session, database_name="DEMO_DEV", schema_name="FRAUD_INTELLIGENCE")
--   mv_v1 = reg.get_model("FRAUD_DETECTION_MODEL").version("V1")
--   mv_v1.create_service(
--       service_name="FRAUD_SCORE_SERVICE_V1",
--       service_compute_pool="FRAUD_INFERENCE_POOL",
--       ingress_enabled=True,
--       autocapture=True,
--       max_instances=1
--   )

-- 4. Deploy V2 (challenger) as inference service
-- Run from Python (notebook cell 4):
--   mv_v2 = reg.get_model("FRAUD_DETECTION_MODEL").version("V20260522_164457")
--   mv_v2.create_service(
--       service_name="FRAUD_SCORE_SERVICE_V2",
--       service_compute_pool="FRAUD_INFERENCE_POOL",
--       ingress_enabled=True,
--       autocapture=True,
--       max_instances=1
--   )

-- 5. Grant endpoint usage to AGENT_DEMO_ROLE
GRANT SERVICE ROLE DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_SERVICE_V1!ALL_ENDPOINTS_USAGE TO ROLE AGENT_DEMO_ROLE;
GRANT SERVICE ROLE DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_SERVICE_V2!ALL_ENDPOINTS_USAGE TO ROLE AGENT_DEMO_ROLE;

-- 6. Create Gateway with A/B traffic split (90% champion, 10% challenger)
USE ROLE AGENT_DEMO_ROLE;
USE SCHEMA DEMO_DEV.FRAUD_INTELLIGENCE;

CREATE OR REPLACE GATEWAY DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_GATEWAY
FROM SPECIFICATION $$
spec:
  type: traffic_split
  split_type: custom
  targets:
  - type: endpoint
    value: DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_SERVICE_V1!inference
    weight: 90
  - type: endpoint
    value: DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_SERVICE_V2!inference
    weight: 10
$$;

-- 7. Get Gateway endpoint URL
-- DESC GATEWAY DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_GATEWAY;

-- 8. Shift traffic after validation (examples):
-- ALTER GATEWAY DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_GATEWAY
-- FROM SPECIFICATION $$
-- spec:
--   type: traffic_split
--   split_type: custom
--   targets:
--   - type: endpoint
--     value: DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_SERVICE_V1!inference
--     weight: 50
--   - type: endpoint
--     value: DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_SERVICE_V2!inference
--     weight: 50
-- $$;

-- 9. Full promotion (100% V2):
-- ALTER GATEWAY DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_GATEWAY
-- FROM SPECIFICATION $$
-- spec:
--   type: traffic_split
--   split_type: custom
--   targets:
--   - type: endpoint
--     value: DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SCORE_SERVICE_V2!inference
--     weight: 100
-- $$;

-- 10. Query inference logs for A/B comparison:
-- SELECT * FROM TABLE(INFERENCE_TABLE('FRAUD_DETECTION_MODEL'));
-- SELECT * FROM TABLE(INFERENCE_TABLE('FRAUD_DETECTION_MODEL', MODEL_VERSION => 'V1', GATEWAY => 'FRAUD_SCORE_GATEWAY'));
-- SELECT * FROM TABLE(INFERENCE_TABLE('FRAUD_DETECTION_MODEL', MODEL_VERSION => 'V20260522_164457', GATEWAY => 'FRAUD_SCORE_GATEWAY'));
