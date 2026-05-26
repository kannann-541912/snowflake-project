# Release Notes: fraud_risk v1.0.0

## Scope

- Initial high-risk fraud model candidate.
- Feature contract `fraud_features_v5`.
- Artifact location `@ML_MODEL_STAGE/fraud_risk/v1.0.0/model.pkl`.

## Validation Summary

- PR-AUC: `0.75` (target >= `0.72`).
- ROC-AUC: `0.93`.
- Staging P95 latency: `260 ms` (target <= `300 ms`).
- Fairness checks completed with no blocking issues.

## Release Plan

1. Register model in staging and run 5% canary.
2. Monitor drift, latency, and false positive rate for 24 hours.
3. Submit production promotion package with evidence.
4. Obtain dual approvals in `MODEL_APPROVALS` for `prod`.
5. Activate model in production only after two APPROVE decisions.

## Rollback Plan

- Set `v1.0.0` inactive in production.
- Reactivate last stable `fraud_risk` version.
- Validate smoke checks and reopen analyst queue controls if needed.
