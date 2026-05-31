-- =============================================================
-- 04_simulate_cost.sql
-- Purpose: Add COST_IS_SIMULATED flag and fill NULL cost rows
--          with simulated values proportional to alert volume.
-- Rate derivation: SUM(TOTAL_CREDITS) / SUM(ALERTS_PROCESSED)
--   from 13 real metering days = 0.025539820812 credits/alert
-- At $3/credit this is ~$0.077 per alert processed.
-- =============================================================
-- INSTRUCTIONS:
-- 1. Run Statement 1 (ALTER) first.
-- 2. Run Statement 2 (UPDATE real rows) second.
-- 3. Run Statement 3 (UPDATE simulated rows) last.
-- 4. Verify: SELECT COST_IS_SIMULATED, COUNT(*)
--            FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
--            GROUP BY 1;
--    Expected: FALSE = 13, TRUE = 66
-- =============================================================

SET CREDIT_COST_USD = 3;

-- Statement 1: Add boolean flag column
ALTER TABLE ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
ADD COLUMN COST_IS_SIMULATED BOOLEAN DEFAULT FALSE;

-- Statement 2: Mark existing real cost rows explicitly
UPDATE ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
SET COST_IS_SIMULATED = FALSE
WHERE TOTAL_CREDITS IS NOT NULL;

-- Statement 3: Fill NULL cost rows with simulated values
-- SIMULATED: proportional to alert volume
-- Rate = 0.025539820812 credits per alert (derived from 13 real days)
UPDATE ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
SET
    TOTAL_CREDITS = ROUND(0.025539820812 * ALERTS_PROCESSED, 4),
    PRODUCTIVE_CREDITS = ROUND(0.025539820812 * ALERTS_PROCESSED * 0.75, 4),
    IDLE_CREDITS = ROUND(0.025539820812 * ALERTS_PROCESSED * 0.25, 4),
    FRAUD_AMOUNT_PER_CREDIT = FRAUD_AMOUNT_PROTECTED /
        NULLIF(ROUND(0.025539820812 * ALERTS_PROCESSED, 4), 0),
    SAR_COST_PER_FILING = ROUND(0.025539820812 * ALERTS_PROCESSED, 4)
        * $CREDIT_COST_USD / NULLIF(SAR_FILED_COUNT, 0),
    COST_IS_SIMULATED = TRUE
WHERE TOTAL_CREDITS IS NULL;

-- Statement 4: Add IDLE_PCT physical column
ALTER TABLE ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
ADD COLUMN IDLE_PCT NUMBER(38,4);

UPDATE ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING
SET IDLE_PCT = IDLE_CREDITS / NULLIF(TOTAL_CREDITS, 0) * 100;

/*Validate simulated cost rows by comparing average cost-per-alert across real vs. simulated dates in FRAUD_INTELLIGENCE_COST_VALUE_MAPPING*/
SELECT COST_IS_SIMULATED, COUNT(*) AS DAYS, SUM(ALERTS_PROCESSED) AS TOTAL_ALERTS, ROUND(SUM(TOTAL_CREDITS), 4) AS TOTAL_CREDITS, ROUND(SUM(TOTAL_CREDITS) / NULLIF(SUM(ALERTS_PROCESSED), 0), 6) AS AVG_CREDITS_PER_ALERT, ROUND(SUM(TOTAL_CREDITS) / NULLIF(SUM(ALERTS_PROCESSED), 0) * 3, 4) AS AVG_COST_PER_ALERT_USD FROM ADMIN_DB.OPS.FRAUD_INTELLIGENCE_COST_VALUE_MAPPING GROUP BY COST_IS_SIMULATED ORDER BY COST_IS_SIMULATED;


/*DISPOSITION = 'CONFIRMED_FRAUD' (655) vs IS_FRAUD_DERIVED = TRUE (644)
Eleven row gap. Analyst confirmed 11 more cases than the ML model flagged. For the demo use DISPOSITION = 'CONFIRMED_FRAUD' as your fraud ground truth — it is the human-verified outcome and the stronger narrative anchor. IS_FRAUD_DERIVED becomes supporting evidence, not primary.
745 NULLs = 53% of alerts unresolved
This is actually a narrative gift. Your demo can show: "half your alert pipeline is still pending — this is where agent-assisted triage has the highest ROI." Do not treat NULLs as missing data. Treat them as the opportunity.*/
SELECT DISPOSITION, COUNT(*) 
FROM DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED 
GROUP BY 1 ORDER BY 2 DESC;

