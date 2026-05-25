-- =============================================================================
-- SBR Intelligence Platform - Semantic View
-- =============================================================================

USE ROLE SBR_ANALYTICS_ROLE;
USE SCHEMA DEMO_DEV.SBR_ANALYTICS;

CREATE OR REPLACE SEMANTIC VIEW SBR_LABOR_SEMANTIC_VIEW
AS
  DEFINE ENTITY LABOR
    BASE_TABLE = DEMO_DEV.SBR_ANALYTICS.GOLD_FACT_LABOR
    PRIMARY_KEY = (EMP_ID, WORK_DATE)

    DIMENSION EMPLOYEE_ID
      EXPRESSION = EMP_ID
      DATA_TYPE = VARCHAR
      SYNONYMS = ('employee', 'worker', 'emp')
      COMMENT = 'Employee identifier'

    DIMENSION WORK_DATE
      EXPRESSION = WORK_DATE
      DATA_TYPE = DATE
      SYNONYMS = ('date', 'day')
      COMMENT = 'Date when work was performed'

    DIMENSION BATCH_ID
      EXPRESSION = BATCH_ID
      DATA_TYPE = VARCHAR
      COMMENT = 'Processing batch identifier'

    FACT PAY_RATE_FACT
      EXPRESSION = PAY_RATE
      DATA_TYPE = NUMBER(10,2)

    METRIC TOTAL_PAYROLL
      EXPRESSION = SUM(PAYROLL_AMOUNT)
      DATA_TYPE = NUMBER(24,2)
      SYNONYMS = ('actual pay', 'payroll', 'total pay')
      COMMENT = 'Total actual payroll amount'

    METRIC TOTAL_EXPECTED
      EXPRESSION = SUM(EXPECTED_PAY)
      DATA_TYPE = NUMBER(24,2)
      SYNONYMS = ('expected pay', 'expected')
      COMMENT = 'Total expected pay based on hours and rate'

    METRIC TOTAL_VARIANCE
      EXPRESSION = SUM(PAYROLL_AMOUNT - EXPECTED_PAY)
      DATA_TYPE = NUMBER(25,2)
      SYNONYMS = ('variance', 'difference', 'gap')
      COMMENT = 'Difference between actual and expected pay'

    METRIC TOTAL_HOURS
      EXPRESSION = SUM(HOURS_WORKED)
      DATA_TYPE = NUMBER(22,2)
      SYNONYMS = ('hours', 'time worked')
      COMMENT = 'Total hours worked'

    METRIC EMPLOYEE_COUNT
      EXPRESSION = COUNT(DISTINCT EMP_ID)
      DATA_TYPE = NUMBER(18,0)
      SYNONYMS = ('headcount', 'employees')
      COMMENT = 'Number of distinct employees'

    METRIC AVG_VARIANCE_PCT
      EXPRESSION = AVG(CASE WHEN EXPECTED_PAY != 0 THEN (PAYROLL_AMOUNT - EXPECTED_PAY) / EXPECTED_PAY * 100 ELSE 0 END)
      DATA_TYPE = NUMBER(38,12)
      SYNONYMS = ('variance percent', 'avg variance')
      COMMENT = 'Average variance percentage'

  DEFINE ENTITY VENDOR
    BASE_TABLE = DEMO_DEV.SBR_ANALYTICS.GOLD_DIM_VENDOR
    PRIMARY_KEY = (VENDOR_ID)

    DIMENSION VENDOR_NAME
      EXPRESSION = VENDOR_NAME
      DATA_TYPE = VARCHAR
      SYNONYMS = ('vendor', 'supplier', 'contractor')
      COMMENT = 'Name of the vendor providing the employee'

    DIMENSION VENDOR_TYPE
      EXPRESSION = VENDOR_TYPE
      DATA_TYPE = VARCHAR
      COMMENT = 'Type of vendor'

    DIMENSION VENDOR_STATUS
      EXPRESSION = STATUS
      DATA_TYPE = VARCHAR
      COMMENT = 'Vendor status'

  DEFINE RELATIONSHIP LABOR_TO_VENDOR
    FROM LABOR(VENDOR_ID) REFERENCES VENDOR(VENDOR_ID);
