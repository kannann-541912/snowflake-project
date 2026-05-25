# Release Runbook (Snowflake ML Models)

## Preconditions

- Approved model spec and model card available.
- Staging validation suite passed.
- Monitoring and alert thresholds configured.
- Rollback plan validated in non-production.

## Release Procedure

1. Confirm target model version is registered and immutable.
2. Create deployment event record with requested environment.
3. Enable canary (recommended 5-10% traffic or scoped workload).
4. Monitor latency, quality, and drift for agreed window.
5. Promote to full traffic only if all SLOs pass.
6. Set previous production model to inactive (do not delete).

## Evidence to Capture

- Approver identity and timestamp.
- Validation report artifact.
- Canary monitoring report.
- Final deployment event status.

## Post-Release

- Review model health daily for first 7 days.
- Log any deviations in incident register.
