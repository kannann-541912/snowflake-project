-- ============================================================
-- Step 3: External Access Integrations (EAIs) and Network Rules
-- Openflow SPCS runtimes require EAIs to reach external sources.
-- Run as ACCOUNTADMIN
--
-- WHY THIS IS STILL SQL: the Snowflake Terraform provider (~> 1.0) has no
-- resource for EXTERNAL ACCESS INTEGRATION, so the EAI must be created here.
-- The network rule and secret it depends on DO have Terraform resources.
--
-- Pick ONE owner for the network rule, not both:
--   - This script (default): creates TPCH_S3_NETWORK_RULE below.
--   - Terraform: set enable_egress_network_rule = true in the relevant
--     environments/*.tfvars, which creates TPCH_EGRESS_RULE in
--     SANDBOX<env_suffix>.TPCH_LANDING. If you do that, delete the CREATE
--     NETWORK RULE below and point ALLOWED_NETWORK_RULES at TPCH_EGRESS_RULE.
-- ============================================================

-- ── S3 access (for ListS3 / FetchS3Object processors) ──────
CREATE OR REPLACE NETWORK RULE TPCH_S3_NETWORK_RULE
    TYPE = HOST_PORT
    MODE = EGRESS
    VALUE_LIST = ('your-data-bucket.s3.amazonaws.com', 's3.amazonaws.com')
    COMMENT = 'Egress to S3 bucket hosting TPCH source files';

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION TPCH_S3_EAI
    ALLOWED_NETWORK_RULES = (TPCH_S3_NETWORK_RULE)
    ENABLED = TRUE
    COMMENT = 'EAI allowing Openflow runtime to reach S3 data sources';

GRANT USAGE ON INTEGRATION TPCH_S3_EAI TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};

-- ── AWS credentials secret (for S3 authentication) ─────────
-- Store AWS credentials as a Snowflake secret instead of hardcoding in the flow.
CREATE OR REPLACE SECRET SANDBOX{{env_suffix}}.TPCH_LANDING.AWS_S3_CREDENTIALS
    TYPE = GENERIC_STRING
    SECRET_STRING = '{"aws_access_key_id": "", "aws_secret_access_key": ""}'
    COMMENT = 'AWS credentials for S3 access from Openflow. Update via Snowsight Secrets.';

GRANT USAGE ON SECRET SANDBOX{{env_suffix}}.TPCH_LANDING.AWS_S3_CREDENTIALS TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};

-- ── (Optional) Kafka / streaming source ────────────────────
-- Uncomment if ingesting from Kafka in addition to S3.
-- CREATE OR REPLACE NETWORK RULE TPCH_KAFKA_NETWORK_RULE
--     TYPE = HOST_PORT
--     MODE = EGRESS
--     VALUE_LIST = ('kafka.internal.example.com:9092')
--     COMMENT = 'Egress to internal Kafka cluster';
--
-- CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION TPCH_KAFKA_EAI
--     ALLOWED_NETWORK_RULES = (TPCH_KAFKA_NETWORK_RULE)
--     ENABLED = TRUE;
--
-- GRANT USAGE ON INTEGRATION TPCH_KAFKA_EAI TO ROLE DATA_PLATFORM_OPENFLOW;
