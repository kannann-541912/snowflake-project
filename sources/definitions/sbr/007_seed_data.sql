-- =============================================================================
-- SBR Intelligence Platform - Seed Data
-- Vendor dimension and sample data for development/testing
-- =============================================================================

USE ROLE SBR_ANALYTICS_ROLE;
USE SCHEMA DEMO_DEV.SBR_ANALYTICS;

-- Vendor Dimension
INSERT INTO GOLD_DIM_VENDOR (VENDOR_ID, VENDOR_NAME, VENDOR_TYPE, CONTACT_NAME, CONTACT_EMAIL, PHONE, CITY, STATE, COUNTRY, CONTRACT_START, CONTRACT_END, STATUS)
VALUES
    ('V001', 'Apex Workforce Solutions', 'Staffing Agency', 'John Smith', 'john@apexworkforce.com', '403-555-0101', 'Calgary', 'AB', 'CA', '2023-01-01', '2025-12-31', 'ACTIVE'),
    ('V002', 'Northern Pipeline Services', 'Contractor', 'Sarah Johnson', 'sarah@nps.com', '780-555-0202', 'Edmonton', 'AB', 'CA', '2023-06-01', '2026-06-30', 'ACTIVE'),
    ('V003', 'Prairie Technical Corp', 'Engineering Firm', 'Mike Wilson', 'mike@prairietech.com', '306-555-0303', 'Saskatoon', 'SK', 'CA', '2024-01-01', '2026-12-31', 'ACTIVE');

-- Batch Control Definitions
INSERT INTO SILVER_BATCH_CONTROL (BATCH_ID, BATCH_NAME, BATCH_TYPE, SCHEDULE_CRON, STATUS)
VALUES
    ('BATCH_SBR_DAILY', 'SBR Daily Labor Ingestion', 'SCHEDULED', '0 6 * * *', 'IDLE'),
    ('BATCH_SBR_SCHEMA_CHECK', 'SBR Schema Validation', 'TRIGGERED', NULL, 'IDLE'),
    ('BATCH_SBR_ANOMALY', 'SBR Anomaly Detection', 'SCHEDULED', '0 7 * * *', 'IDLE');

-- Task Registry (Pipeline DAG)
INSERT INTO SILVER_TASK_REGISTRY (TASK_ID, TASK_NAME, TASK_TYPE, BATCH_ID, EXECUTION_ORDER, TARGET_OBJECT, SOURCE_OBJECT)
VALUES
    ('T001', 'Ingest Raw Files to Bronze', 'COPY_INTO', 'BATCH_SBR_DAILY', 1, 'BRZ_LABOR', '@SBR_SOURCE_STAGE'),
    ('T002', 'Schema Validation', 'PROCEDURE', 'BATCH_SBR_DAILY', 2, 'OPS_SCHEMA_GAPS', 'BRZ_LABOR'),
    ('T003', 'Cleanse and Type Cast to Silver', 'SQL', 'BATCH_SBR_DAILY', 3, 'SLV_LABOR', 'BRZ_LABOR'),
    ('T004', 'Data Quality Checks', 'SQL', 'BATCH_SBR_DAILY', 4, 'OPS_DATA_QUALITY_ISSUES', 'SLV_LABOR'),
    ('T005', 'Build Gold Fact', 'SQL', 'BATCH_SBR_DAILY', 5, 'GLD_FACT_LABOR', 'SLV_LABOR'),
    ('T006', 'Anomaly Detection Scoring', 'SQL', 'BATCH_SBR_DAILY', 6, 'GLD_FACT_LABOR', 'GLD_FACT_LABOR'),
    ('T007', 'Audit Metrics Capture', 'PROCEDURE', 'BATCH_SBR_DAILY', 7, 'OPS_AUDIT_METRICS', 'GLD_FACT_LABOR');

-- Task Dependencies
INSERT INTO SILVER_TASK_DEPENDENCY (TASK_ID, DEPENDS_ON_TASK_ID, DEPENDENCY_TYPE)
VALUES
    ('T002', 'T001', 'HARD'),
    ('T003', 'T002', 'HARD'),
    ('T004', 'T003', 'HARD'),
    ('T005', 'T004', 'HARD'),
    ('T006', 'T005', 'HARD'),
    ('T007', 'T006', 'HARD');
