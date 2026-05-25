-- =============================================================================
-- SBR Intelligence Platform - Stages & File Formats
-- =============================================================================

USE ROLE SBR_ANALYTICS_ROLE;
USE SCHEMA DEMO_DEV.SBR_ANALYTICS;

-- File Formats
CREATE OR REPLACE FILE FORMAT CSV_FMT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('\\N')
    COMMENT = 'Standard CSV format for vendor labor files';

CREATE OR REPLACE FILE FORMAT RAW_TEXT
    TYPE = 'CSV'
    RECORD_DELIMITER = 'NONE'
    FIELD_DELIMITER = 'NONE'
    COMMENT = 'Raw text format for reading entire file as single field';

-- Stages
CREATE OR REPLACE STAGE SBR_SOURCE_STAGE
    COMMENT = 'Internal stage for vendor CSV source files';

CREATE OR REPLACE STAGE SBR_SEMANTIC_STAGE
    COMMENT = 'Internal stage for semantic model YAML files';

CREATE OR REPLACE STAGE SBR_STREAMLIT_STAGE
    COMMENT = 'Internal stage for SBR Intelligence Streamlit app files';

CREATE OR REPLACE STAGE SHARED_STREAMLIT_THEME
    COMMENT = 'Internal stage for shared Streamlit theme (styles.py, config.toml)';

CREATE OR REPLACE STAGE STREAMLIST_APP_STAGE
    COMMENT = 'Internal stage for legacy Streamlit app';
