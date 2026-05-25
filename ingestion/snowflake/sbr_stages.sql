-- =============================================================================
-- SBR Intelligence Platform - Stages for Source Ingestion
-- =============================================================================

USE ROLE SBR_ANALYTICS_ROLE;
USE SCHEMA DEMO_DEV.SBR_ANALYTICS;

-- Source stage structure:
-- @SBR_SOURCE_STAGE/
--   v001/   <- Apex Workforce Solutions files
--     apex_labor_jan2025.csv
--     apex_labor_feb2025.csv
--     apex_labor_mar2025.csv
--   v002/   <- Northern Pipeline Services files
--     nps_timesheet_jan2025.csv
--     nps_timesheet_feb2025.csv
--   v003/   <- Prairie Technical Corp files
--     prairie_labor_jan2025.csv
--     prairie_labor_feb2025.csv
--     prairie_labor_mar2025.csv

CREATE OR REPLACE STAGE SBR_SOURCE_STAGE
    COMMENT = 'Internal stage for vendor CSV source files. Organized by vendor_id subfolder.';
