# Operating Model for Production ML Lifecycle

## Lifecycle Stages

1. **Intake**: define business objective, KPI, owner, and risk tier.
2. **Build**: train and validate candidate model in development.
3. **Qualify**: evaluate performance, fairness, and stability thresholds.
4. **Register**: publish immutable model version metadata and lineage.
5. **Deploy**: promote through staging to production with approvals.
6. **Monitor**: track quality, drift, latency, and cost.
7. **Retrain**: trigger retraining based on policy or degradation.
8. **Retire**: deprecate unused or non-compliant model versions.

## Roles and Responsibilities

- **Model Owner**: accountable for model outcomes and documentation.
- **ML Engineer**: implements training, packaging, and deployment assets.
- **Data Engineer**: ensures feature/data contract reliability.
- **Platform Owner**: maintains Snowflake compute, access, and CI/CD.
- **Risk/Compliance Reviewer**: approves high-risk model promotions.

## Promotion Gates

- **Dev -> Staging**
  - Unit and data validation checks pass.
  - Baseline model card completed.
  - Lineage and reproducibility evidence attached.
- **Staging -> Production**
  - Performance SLOs pass against holdout and replay datasets.
  - Operational runbook and rollback plan approved.
  - Monitoring and alerts enabled before cutover.

## Minimum Metadata for Each Model Version

- Model name, semantic version, owner, and domain.
- Training window and input feature contract version.
- Hyperparameters, evaluation metrics, and threshold outcomes.
- Artifact location, deployment timestamp, and approver.
- Lineage references (dataset versions, code revision).

## Production Control Policies

- Use separate Snowflake roles and warehouses per environment.
- Enforce least-privilege access for training and inference objects.
- Make model registration immutable per released version.
- Require dual approval for high-risk model category deployment.
- Record all production promotions and rollbacks in audit logs.
