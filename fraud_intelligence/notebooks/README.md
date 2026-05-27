# Fraud Detection Model — Training Notebook

## Overview

This notebook trains and registers the `FRAUD_DETECTION_MODEL` (XGBClassifier) in the Snowflake ML Model Registry. It supports both initial training and retraining with decision feedback.

## Model Purpose

Binary classification predicting whether a transaction is fraudulent (`TARGET_LABEL = 1`) or non-fraudulent (`TARGET_LABEL = 0`).

## Data Sources

| Source | Purpose |
|--------|---------|
| `DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ML_TRAINING_SET` | Primary training features and labels |
| `DEMO_DEV.FRAUD_INTELLIGENCE.BRZ_RAW_ALERTS` | Decision feedback (DISPOSITION, SAR_FILED) for label enrichment |
| `DEMO_DEV.FRAUD_INTELLIGENCE.SLV_MODEL_PERFORMANCE_LOG` | Historical model metrics for comparison |
| `DEMO_DEV.FRAUD_INTELLIGENCE.SLV_FRAUD_MODEL_METADATA` | Model registry metadata |

## Feature Schema (36 features)

**Numeric (14):** TRANSACTION_AMOUNT, ACCOUNT_AGE_DAYS, CREDIT_LIMIT, CURRENT_BALANCE, UTILIZATION_RATIO, ADDRESS_CHANGE_COUNT, CUSTOMER_TENURE_DAYS, PRIOR_ALERT_COUNT_CUSTOMER, ALERT_WITHIN_7D, TXN_COUNT_1H, TXN_COUNT_24H, TXN_AMOUNT_1H, TXN_AMOUNT_24H, DISTINCT_MERCHANTS_24H

**Boolean (3):** KYC_COMPLETE, IS_SYNTHETIC_FLAG, IS_MERGER_DUP_FLAG

**One-Hot Encoded (19):** TRANSACTION_TYPE (4), MERCHANT_CATEGORY (8), CHANNEL (3), ACCOUNT_TYPE (2), RISK_SEGMENT (2)

## Label Sourcing

1. **First-time training:** Uses `TARGET_LABEL` from `GLD_ML_TRAINING_SET`
2. **Retraining:** Merges analyst decisions from `BRZ_RAW_ALERTS`:
   - `DISPOSITION = 'CONFIRMED_FRAUD'` or `SAR_FILED = TRUE` → Fraud (1)
   - Existing `TARGET_LABEL` values retained for non-alerted transactions

## Prerequisites

- **Feedback write-back is NOT yet implemented** in the Streamlit app. Analyst decision buttons currently only show toasts without persisting to tables.
- Once implemented, this notebook will automatically pick up fraud labels on retraining.

## How to Retrain

1. Ensure new data has been loaded into `GLD_ML_TRAINING_SET`
2. (Optional) Verify analyst decisions exist in `BRZ_RAW_ALERTS`
3. Run all cells in the notebook
4. Check `SLV_MODEL_PERFORMANCE_LOG` for the new version's metrics
5. New model version is automatically registered in the ML Registry

## Versioning

- Versions follow pattern: `V{YYYYMMDD_HHMMSS}` (e.g., `V20260522_143000`)
- Each run creates a new version; prior versions are retained
- Metadata table is updated to point to the latest active version

## Role

Requires `AGENT_DEMO_ROLE` with access to schema `DEMO_DEV.FRAUD_INTELLIGENCE`.
