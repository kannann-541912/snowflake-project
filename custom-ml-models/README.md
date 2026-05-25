# custom-ml-models — Developer Guide

This directory is the production-ready home for building, registering, deploying, and monitoring custom ML models in Snowflake. It covers the full model lifecycle from intake to retirement.

## Directory Layout

```
custom-ml-models/
├── OPERATING_MODEL.md          # Lifecycle stages, roles, promotion gates, control policies
├── lifecycle/
│   └── checklist.md            # Per-model stage-by-stage delivery checklist
├── environments/
│   ├── dev.yml                 # Dev environment: DB, warehouse, role, SLO thresholds
│   ├── staging.yml             # Staging environment: stricter thresholds, approval required
│   └── prod.yml                # Production environment: tightest thresholds, dual control
├── snowflake/
│   └── sql/
│       ├── 001_setup_mlops_foundation.sql    # MODEL_REGISTRY + MODEL_DEPLOYMENT_EVENTS tables
│       ├── 002_model_registry_and_lineage.sql # MODEL_LINEAGE, MODEL_APPROVALS, V_ACTIVE_MODELS
│       └── 003_monitoring_views_and_alerts.sql # MODEL_PREDICTION_LOG, V_MODEL_HEALTH_DAILY
├── templates/
│   ├── model_spec_template.yml  # Starter spec — copy this for every new model
│   └── model_card_template.md   # Governance card — required before staging promotion
├── runbooks/
│   ├── release_runbook.md       # Step-by-step production release procedure
│   └── incident_and_rollback.md # Rollback triggers, steps, and post-incident actions
└── examples/
    ├── churn-risk-v1/           # Medium-risk example — standard approval flow
    └── fraud-risk-v1/           # High-risk example — dual-control production activation
```

## Quickstart — Adding a New Model

### Step 1 — Create your model's folder

```bash
mkdir -p custom-ml-models/my-model-v1/snowflake/sql
```

### Step 2 — Fill in the spec and model card

```bash
cp custom-ml-models/templates/model_spec_template.yml  custom-ml-models/my-model-v1/model_spec.yml
cp custom-ml-models/templates/model_card_template.md   custom-ml-models/my-model-v1/model_card.md
```

Edit both files — replace every `<placeholder>` with real values. The spec must pass `validate-ml-models` in CI before the PR can merge.

### Step 3 — Apply the SQL foundation (first time only per environment)

```bash
pip install snowflake-cli

# Apply in order — dev first, then staging, then prod
snow sql -f custom-ml-models/snowflake/sql/001_setup_mlops_foundation.sql -c dev
snow sql -f custom-ml-models/snowflake/sql/002_model_registry_and_lineage.sql -c dev
snow sql -f custom-ml-models/snowflake/sql/003_monitoring_views_and_alerts.sql -c dev
```

The foundation SQL creates all MLOps tables and views in `ML_DEV.MLOPS` (dev) or `ML_PROD.MLOPS` (prod). CI runs this automatically via the `deploy-ml-models` job.

### Step 4 — Register your model version in Snowflake

Copy the registration SQL from an example and adapt it:

```bash
cp custom-ml-models/examples/churn-risk-v1/snowflake/sql/001_register_model.sql \
   custom-ml-models/my-model-v1/snowflake/sql/001_register_model.sql
```

Edit the file — update `MODEL_NAME`, `MODEL_VERSION`, `ARTIFACT_URI`, `METRICS`, and `ENVIRONMENT`.

Run it against staging after your training run completes:

```bash
snow sql -f custom-ml-models/my-model-v1/snowflake/sql/001_register_model.sql -c default
```

### Step 5 — Follow the lifecycle checklist

Work through `lifecycle/checklist.md` stage by stage. No model version should reach production without all gates checked.

## Environment Configs

The files in `environments/` define the Snowflake targets and SLO thresholds for each environment. Reference them in deployment scripts to avoid hardcoding.

| Environment | Database | Approval required | Drift threshold | Quality floor |
|-------------|----------|-----------------|-----------------|---------------|
| dev | `ML_DEV` | No | 0.25 | 0.70 |
| staging | `ML_STAGING` | Yes | 0.20 | 0.75 |
| prod | `ML_PROD` | Yes + dual control (high-risk) | 0.15 | 0.80 |

## Risk Tiers

| Tier | Dual approval in prod | Human-in-the-loop | Canary % |
|------|----------------------|-------------------|----------|
| low | No | No | 10% |
| medium | No | Recommended | 10% |
| high | Yes | Required | 5% |

See `examples/churn-risk-v1/` (medium) and `examples/fraud-risk-v1/` (high) for full worked examples.

## Monitoring a Deployed Model

Query the health view in Snowflake:

```sql
SELECT *
FROM ML_PROD.MLOPS.V_MODEL_HEALTH_DAILY
WHERE EVENT_DAY >= CURRENT_DATE - 7
ORDER BY EVENT_DAY DESC, MODEL_NAME;
```

See active models:

```sql
SELECT * FROM ML_PROD.MLOPS.V_ACTIVE_MODELS;
```

## CI/CD Integration

| Workflow | Trigger | What runs |
|----------|---------|-----------|
| `validate.yml` | PR to `main` | YAML spec validation, required field checks, SQL script structure checks |
| `deploy.yml` | Push to `main` | SQL foundation scripts applied to target environment (ML_DEV or ML_PROD) |

The `deploy-ml-models` job runs in parallel with `deploy-ingestion` — both depend on `deploy-dcm` completing first.

## Runbooks

| Situation | Runbook |
|-----------|---------|
| Releasing a model to production | `runbooks/release_runbook.md` |
| Incident or quality degradation | `runbooks/incident_and_rollback.md` |
