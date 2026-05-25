# Release Notes: churn_risk v1.0.0

## Scope

- Initial production candidate for churn risk scoring.
- Uses feature contract `customer_features_v3`.
- Introduces model artifact at `@ML_MODEL_STAGE/churn_risk/v1.0.0/model.pkl`.

## Validation Summary

- Offline AUC-ROC: `0.86` (target >= `0.84`).
- PR-AUC: `0.49`.
- Staging P95 latency: `870 ms` (target <= `900 ms`).
- No blocking fairness issues identified in approval review.

## Release Plan

1. Register version in staging registry.
2. Start 10% canary traffic.
3. Observe health signals for 24 hours.
4. Promote to full staging if no threshold breaches.
5. Submit production promotion request with evidence.

## Rollback Plan

- Deactivate `v1.0.0`.
- Reactivate last known healthy version from `V_ACTIVE_MODELS` history.
- Confirm smoke checks and close release incident if triggered.
