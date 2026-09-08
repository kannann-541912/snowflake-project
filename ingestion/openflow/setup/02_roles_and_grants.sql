-- ============================================================
-- Step 2: Roles and grants for Openflow SPCS deployment
-- Run as ACCOUNTADMIN
-- Environment naming: {{env_suffix}} resolved by deployment tooling.
-- ============================================================

-- Dedicated role for the Openflow runtime.
-- This role is attached to the Openflow session token — no service user or key-pair needed.
CREATE ROLE IF NOT EXISTS DATA_PLATFORM_OPENFLOW{{env_suffix}}
    COMMENT = 'Role used by TPCH Openflow SPCS runtime for data ingestion';

-- Allow the runtime role to land data into the landing schema
GRANT USAGE ON DATABASE SANDBOX{{env_suffix}} TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};
GRANT USAGE ON SCHEMA SANDBOX{{env_suffix}}.TPCH_LANDING TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};
GRANT USAGE ON SCHEMA SANDBOX{{env_suffix}}.TPCH TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};

-- Stage access (for COPY INTO from S3 stage)
GRANT READ ON STAGE SANDBOX{{env_suffix}}.TPCH_LANDING.CUSTOMERS_STAGE TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};
GRANT READ ON STAGE SANDBOX{{env_suffix}}.TPCH_LANDING.ORDERS_STAGE TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};

-- Table write access — landing tables only (principle of least privilege)
GRANT INSERT, SELECT ON TABLE SANDBOX{{env_suffix}}.TPCH_LANDING.CUSTOMERS_RAW TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};
GRANT INSERT, SELECT ON TABLE SANDBOX{{env_suffix}}.TPCH_LANDING.ORDERS_RAW TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};

-- Allow Openflow to call Snowpipe Streaming (PutSnowflakeStreaming processor)
GRANT CREATE PIPE ON SCHEMA SANDBOX{{env_suffix}}.TPCH_LANDING TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};

-- Warehouse for ad-hoc operations (Openflow processors that issue SQL)
GRANT USAGE ON WAREHOUSE ANALYTICS_WH{{env_suffix}} TO ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}};

-- Grant role to ACCOUNTADMIN for manageability
GRANT ROLE DATA_PLATFORM_OPENFLOW{{env_suffix}} TO ROLE ACCOUNTADMIN;
