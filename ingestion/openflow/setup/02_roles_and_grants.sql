-- ============================================================
-- Step 2: Roles and grants for Openflow SPCS deployment
-- Run as ACCOUNTADMIN or SYSADMIN
-- ============================================================

-- Dedicated role for the Openflow runtime.
-- This role is attached to the Openflow session token — no service user or key-pair needed.
CREATE ROLE IF NOT EXISTS DATA_PLATFORM_OPENFLOW
    COMMENT = 'Role used by TPCH Openflow SPCS runtime for data ingestion';

-- Allow the runtime role to land data into the landing schema
GRANT USAGE ON DATABASE SANDBOX TO ROLE DATA_PLATFORM_OPENFLOW;
GRANT USAGE ON SCHEMA SANDBOX.TPCH_LANDING TO ROLE DATA_PLATFORM_OPENFLOW;
GRANT USAGE ON SCHEMA SANDBOX.TPCH TO ROLE DATA_PLATFORM_OPENFLOW;

-- Stage access (for COPY INTO from S3 stage)
GRANT READ ON STAGE SANDBOX.TPCH_LANDING.CUSTOMERS_STAGE TO ROLE DATA_PLATFORM_OPENFLOW;
GRANT READ ON STAGE SANDBOX.TPCH_LANDING.ORDERS_STAGE TO ROLE DATA_PLATFORM_OPENFLOW;

-- Table write access — landing tables only (principle of least privilege)
GRANT INSERT, SELECT ON TABLE SANDBOX.TPCH_LANDING.CUSTOMERS_RAW TO ROLE DATA_PLATFORM_OPENFLOW;
GRANT INSERT, SELECT ON TABLE SANDBOX.TPCH_LANDING.ORDERS_RAW TO ROLE DATA_PLATFORM_OPENFLOW;

-- Allow Openflow to call Snowpipe Streaming (PutSnowflakeStreaming processor)
GRANT CREATE PIPE ON SCHEMA SANDBOX.TPCH_LANDING TO ROLE DATA_PLATFORM_OPENFLOW;

-- Warehouse for ad-hoc operations (Openflow processors that issue SQL)
GRANT USAGE ON WAREHOUSE ANALYTICS_WH TO ROLE DATA_PLATFORM_OPENFLOW;

-- Grant role to SYSADMIN for manageability
GRANT ROLE DATA_PLATFORM_OPENFLOW TO ROLE SYSADMIN;
