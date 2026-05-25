# Model Card: `fraud_risk`

## Overview

- **Version**: `v1.0.0`
- **Owner**: `ml-fraud-team`
- **Use case**: real-time fraud risk scoring for card/payment transactions
- **Risk tier**: `high`

## Intended Use

- Supports fraud analyst triage and risk-based step-up verification.
- Not intended for fully automated account closure without analyst policy checks.
- Requires human review for scores above policy critical threshold.

## Data and Features

- Sources:
  - `ANALYTICS.PAYMENTS.TRANSACTIONS_ENRICHED`
  - `ANALYTICS.PAYMENTS.ACCOUNT_BEHAVIOR_DAILY`
- Feature contract: `fraud_features_v5`.
- Label definition: confirmed fraud event in adjudication window.

## Performance

- Primary metric: PR-AUC = `0.75` (target >= `0.72`).
- Secondary metric: ROC-AUC = `0.93`.
- P95 scoring latency target: `< 300 ms`.

## Risk and Fairness

- Segment checks performed across country and merchant categories.
- Critical failure mode: false positives impacting legitimate transactions.
- Mitigations:
  - Dynamic thresholding by risk policy.
  - Human-in-the-loop review for highest-risk bucket.
  - Daily fairness and false positive monitoring.

## Operations

- Deployment path: dev -> staging -> prod with dual approval in prod.
- Monitoring signals: PR-AUC proxy, false positive rate, drift score, p95 latency, alert volume.
- Retraining trigger: drift > `0.10` or false positive rate > policy threshold.
- Rollback: immediate revert to last known stable version on severe incident.
