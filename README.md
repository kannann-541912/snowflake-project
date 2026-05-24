# snowflake-project

Enterprise-grade Snowflake data platform — DCM, Cortex Agent lifecycle, ingestion pipeline, and dbt transforms.

## Repository Layout

```
snowflake-project/
├── sources/            # DCM declarative object definitions (tables, views, warehouse, roles)
├── agent/              # Cortex Agent — enterprise lifecycle
│   ├── specs/          # Versioned agent specs (v1, v2, …)
│   ├── evals/          # LLM-as-judge evaluation suite (CORTEX.AI_JUDGE)
│   ├── prompts/        # Orchestration + response prompt files
│   ├── monitoring/     # Usage queries, alert policies
│   ├── agent_spec.json # Current canonical spec
│   └── instructions.md # Legacy instructions (superseded by prompts/)
├── ingestion/          # Data ingestion pipeline
│   ├── airflow/        # Airflow DAGs (customers, orders, orchestrator)
│   ├── snowflake/      # Stages, Streams, Task DAG (native Snowflake orchestration)
│   ├── snowpark/       # Snowpark Python stored procedures
│   └── config/         # Pipeline configuration
├── dbt/                # dbt transform project
│   ├── models/staging/ # Source-aligned views
│   ├── models/intermediate/ # Ephemeral joins
│   ├── models/marts/   # Incremental fact tables (Cortex Agent + BI layer)
│   ├── snapshots/      # Type-2 SCD snapshots
│   ├── macros/         # Custom macros (schema naming, Snowflake utils)
│   └── tests/generic/  # Custom generic tests
├── streamlit/          # Streamlit in Snowflake dashboard
├── scripts/            # Deploy + validate scripts
└── .github/workflows/  # CI/CD (PR validation + main-branch deploy)
```

## Component Overview

### DCM (Declarative Change Management)
Manages Snowflake infrastructure objects declaratively — warehouse, tables, views, roles/grants.
Supports DEV and PROD targets with Jinja templating.

```bash
snow dcm plan --target DEV -c ci
snow dcm deploy --target PROD -c prod --alias "gh-<sha>"
```

### Cortex Agent — Enterprise Lifecycle

| Component | Path | Purpose |
|-----------|------|---------|
| Spec versioning | `agent/specs/v1/` | Immutable snapshots of deployed specs |
| Evals | `agent/evals/` | Ground-truth Q&A + AI Judge scoring via `CORTEX.AI_JUDGE` |
| Prompts | `agent/prompts/` | Versioned orchestration + response prompts |
| Monitoring | `agent/monitoring/` | Usage SQL + alert policy for Snowflake Alerts |

```bash
# Deploy agent
python scripts/deploy_agent.py | snow sql -c prod --stdin

# Run evaluations
python agent/evals/run_evals.py
python agent/evals/run_evals.py --question-id GT-001
python agent/evals/run_evals.py --dry-run
```

### Ingestion Pipeline (Airflow + Snowflake-native)

```
S3 → Airflow (COPY INTO) → Landing Tables → Streams → Snowflake Task DAG → Curated Tables
```

- **Airflow DAGs**: `ingest_customers`, `ingest_orders`, `pipeline_orchestrator`
- **Snowflake Tasks**: Native DAG with `SYSTEM$STREAM_HAS_DATA` guards
- **Snowpark**: Complex transforms deployed as stored procedures

```bash
# Deploy Snowflake objects
snow sql -f ingestion/snowflake/stages.sql -c prod
snow sql -f ingestion/snowflake/streams.sql -c prod
snow sql -f ingestion/snowflake/tasks.sql -c prod
```

### dbt

```bash
cd dbt
dbt deps          # Install packages (dbt_utils, dbt_expectations, elementary, …)
dbt run           # Run all models
dbt test          # Run all tests
dbt snapshot      # Run SCD snapshots
```

## CI/CD Pipeline

### PR Validation (`.github/workflows/validate.yml`)
| Job | What it checks |
|-----|---------------|
| `validate-dcm` | DCM analyze + plan against DEV |
| `validate-agent` | Spec JSON structure, deploy dry-run, eval dry-run |
| `validate-dbt` | `dbt compile`, `dbt parse` |
| `validate-ingestion` | Airflow DAG syntax check |
| `lint-naming` | UPPER_SNAKE_CASE on all DCM definitions |
| `validate-streamlit` | Python AST parse |
| `security-scan` | Bandit + Gitleaks |

### Main Branch Deploy (`.github/workflows/deploy.yml`)
Ordered pipeline with dependency gates:
```
deploy-dcm → deploy-ingestion → deploy-dbt → deploy-streamlit
                                           → deploy-agent → run-agent-evals
```

## Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier |
| `SNOWFLAKE_USER` | Service account username |
| `SNOWFLAKE_PRIVATE_KEY` | RSA private key (PEM format) for JWT auth |
| `OPENFLOW_RUNTIME_URL` | Openflow SPCS runtime URL (set after initial deployment) |
| `S3_BUCKET` | S3 bucket name hosting source files |
