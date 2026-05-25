# Incident and Rollback Runbook

## Trigger Conditions

- P95 latency exceeds SLO for two consecutive windows.
- Drift score crosses threshold in production.
- Quality signal drops below floor.
- Critical upstream data contract break detected.

## Incident Response

1. Declare incident with severity and owner.
2. Freeze new promotions for affected model family.
3. Gather evidence from model health and deployment events.
4. Classify root cause: data, model, infra, or dependency.
5. Communicate impact and ETA to stakeholders.

## Rollback Procedure

1. Identify last known healthy model version.
2. Mark current version inactive for production routing.
3. Activate previous version and validate smoke checks.
4. Confirm restored service and close incident timeline.

## Recovery and Prevention

- Document root cause and remediation actions.
- Add guardrail tests or alert improvements.
- Update retraining and release policy if needed.
