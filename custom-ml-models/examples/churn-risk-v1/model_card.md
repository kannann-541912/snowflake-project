# Model Card: `churn_risk`

## Overview

- **Version**: `v1.0.0`
- **Owner**: `ml-retention-team`
- **Use case**: churn propensity scoring for proactive retention outreach
- **Risk tier**: `medium`

## Intended Use

- Supports prioritization in customer success workflows.
- Intended for decision support, not fully automated account actions.
- Excludes enterprise-custom-contract customers from scoring output.

## Data and Features

- Sources:
  - `ANALYTICS.CUSTOMER_360.SUBSCRIPTION_SNAPSHOT_DAILY`
  - `ANALYTICS.CUSTOMER_360.SUPPORT_ACTIVITY_DAILY`
- Feature contract: `customer_features_v3`.
- Label definition: customer churn event within next 30 days.

## Performance

- Primary metric: AUC-ROC = `0.86` on holdout period.
- Secondary metric: PR-AUC = `0.49`.
- P95 scoring latency target: `< 900 ms`.

## Risk and Fairness

- Regional segment performance reviewed; no critical disparity found beyond policy tolerance.
- Failure mode: false positives during planned billing changes.
- Mitigation: suppress scored output for known billing migration cohorts.

## Operations

- Deployment path: dev -> staging -> prod.
- Monitoring signals: drift score, daily AUC proxy, latency p95, scoring volume.
- Retraining trigger: drift > `0.15` or quality floor breach for two weekly windows.
- Rollback: revert to last active model version recorded in `MODEL_REGISTRY`.
