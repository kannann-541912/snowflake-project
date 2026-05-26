-- ============================================================
-- Step 1: Create compute pool for Openflow - Snowflake Deployment
-- Run as ACCOUNTADMIN
-- ============================================================

-- Compute pool that backs the Openflow SPCS deployment.
-- Size this based on expected throughput; start with STANDARD_1 and scale up.
CREATE COMPUTE POOL IF NOT EXISTS TPCH_OPENFLOW_POOL
    MIN_NODES = 1
    MAX_NODES = 3
    INSTANCE_FAMILY = CPU_X64_S   -- STANDARD_1 equivalent; upgrade to M for higher throughput
    AUTO_RESUME = TRUE
    AUTO_SUSPEND_SECS = 300
    COMMENT = 'Compute pool for TPCH Openflow SPCS deployment';

-- Grant the DATA_PLATFORM_OPENFLOW role usage on the compute pool
GRANT USAGE ON COMPUTE POOL TPCH_OPENFLOW_POOL TO ROLE DATA_PLATFORM_OPENFLOW;
