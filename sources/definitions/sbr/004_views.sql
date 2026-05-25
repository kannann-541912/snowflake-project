-- =============================================================================
-- SBR Intelligence Platform - Views
-- =============================================================================

USE ROLE SBR_ANALYTICS_ROLE;
USE SCHEMA DEMO_DEV.SBR_ANALYTICS;

CREATE OR REPLACE VIEW GOLD_MART_LABOR_V
COMMENT = 'Reporting mart view joining labor facts with vendor dimensions for BI consumption.'
AS
SELECT
    f.EMP_ID,
    f.WORK_DATE,
    f.HOURS_WORKED,
    f.PAYROLL_AMOUNT AS ACTUAL_PAY,
    f.EXPECTED_PAY,
    f.PAYROLL_AMOUNT - f.EXPECTED_PAY AS VARIANCE_AMOUNT,
    CASE WHEN f.EXPECTED_PAY != 0
         THEN ROUND((f.PAYROLL_AMOUNT - f.EXPECTED_PAY) / f.EXPECTED_PAY * 100, 2)
         ELSE 0 END AS VARIANCE_PCT,
    f.BATCH_ID,
    f.VENDOR_ID,
    v.VENDOR_NAME,
    v.VENDOR_TYPE,
    v.CONTACT_NAME AS VENDOR_CONTACT,
    v.CONTACT_EMAIL AS VENDOR_EMAIL,
    v.STATUS AS VENDOR_STATUS
FROM DEMO_DEV.SBR_ANALYTICS.GOLD_FACT_LABOR f
LEFT JOIN DEMO_DEV.SBR_ANALYTICS.GOLD_DIM_VENDOR v ON f.VENDOR_ID = v.VENDOR_ID;
