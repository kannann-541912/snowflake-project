# Model Lifecycle Checklist

Use this checklist per model version.

## Intake

- [ ] Problem statement and decision impact documented.
- [ ] Business KPI and technical metric targets agreed.
- [ ] Owner, backup owner, and review stakeholders assigned.
- [ ] Risk tier classified (low, medium, high).

## Build

- [ ] Training data contract version captured.
- [ ] Feature engineering logic versioned.
- [ ] Experiment runs tracked and reproducible.
- [ ] Candidate model artifacts stored in governed location.

## Qualify

- [ ] Offline performance thresholds met.
- [ ] Drift sensitivity and robustness checks completed.
- [ ] Bias/fairness checks completed for sensitive features.
- [ ] Load or latency test passed for target SLO.

## Register

- [ ] Model spec submitted from template.
- [ ] Model card completed and reviewed.
- [ ] Registry record created with immutable version.
- [ ] Lineage links stored (code, data, artifact).

## Deploy

- [ ] Staging deploy successful with no critical issues.
- [ ] Production approval(s) recorded.
- [ ] Monitoring views and alert policy active.
- [ ] Rollback runbook tested in non-prod.

## Operate

- [ ] Daily quality checks active.
- [ ] Weekly drift and cost report reviewed.
- [ ] Monthly model and feature contract review completed.
- [ ] Retraining trigger policy monitored.
