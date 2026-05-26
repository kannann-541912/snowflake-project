# Snowflake Account Operations Platform

> A unified engineering platform for managing a production Snowflake account across three operational disciplines: **DataOps**, **MLOps**, and **AgentOps**.

This repository is the single source of truth for all Snowflake infrastructure, data pipelines, ML model lifecycle, AI agent operations, and observability dashboards. Every object, model, and agent that runs in the account is declared, versioned, tested, and deployed from here.

---

## Platform Pillars

| Pillar | Scope | Key Components |
|--------|-------|---------------|
| **DataOps** | Infrastructure, ingestion, and transformation | DCM (declarative objects), Snowflake Openflow, Snowflake Task DAG, dbt |
| **MLOps** | Custom ML model lifecycle | Model registry, lineage, monitoring, governance, deployment controls |
| **AgentOps** | AI agent operations | Cortex Agent lifecycle, LLM evaluation, prompt versioning, usage observability |
| **Dashboards** | Operational visibility | Multi-app Streamlit in Snowflake (SiS) |

> **On AgentOps**: the term describes the operational discipline of managing AI agent lifecycles in production — covering spec versioning, deployment, LLM-as-judge evaluation, prompt governance, and usage monitoring. It is distinct from AIOps (AI for IT infrastructure operations) and LLMOps (base model training and fine-tuning). AgentOps is the right label here because the unit being operated is a deployed Snowflake Cortex Agent, not an ML model or an IT system.

---

## Snowflake Account

| Setting | Value |
|---------|-------|
| Account | `xna38553.east-us-2.azure` |
| Host | `xna38553.east-us-2.azure.snowflakecomputing.com` |
| Auth | Programmatic Access Token (PAT) |
| Primary database | `SANDBOX` |
| Primary schema | `TPCH` / `TPCH_LANDING` |
| ML databases | `ML_DEV` / `ML_STAGING` / `ML_PROD` |
| Warehouse | `ANALYTICS_WH` |
| Service user | `MCP_SERVICE_USER` |
| Default role | `ACCOUNTADMIN` |

### Local Setup

```bash
# 1. Install the Snowflake CLI
pip install snowflake-cli

# 2. Copy the connection template and fill in your PAT
cp config.toml.example config.toml
# Edit config.toml — generate/rotate PATs in Snowsight:
#   Admin → Security → Programmatic Access Tokens
# NEVER commit config.toml — it is gitignored.

# 3. Verify connectivity
snow connection test -c default
```

---

## Repository Layout

```
snowflake-project/
│
├── config.toml.example          # Connection template — copy to config.toml
├── manifest.yml                 # DCM project config (DEV / CI / PROD targets)
│
├── sources/                     # ── DataOps: Declarative infrastructure ──
│   └── definitions/
│       ├── infrastructure.sql   # DEFINE WAREHOUSE (size, suspend policy)
│       ├── tables.sql           # DEFINE TABLE — CUSTOMERS, ORDERS
│       ├── views.sql            # DEFINE VIEW  — CUSTOMER_ORDER_SUMMARY
│       └── access.sql           # DEFINE ROLE + GRANT — DATA_READER
│
├── ingestion/                   # ── DataOps: Ingestion pipeline ──
│   ├── openflow/                # Snowflake Openflow (NiFi-based, SPCS-hosted)
│   │   ├── setup/               # Compute pool, roles, EAIs (one-time admin)
│   │   ├── flows/               # nipyapi flow definitions (Python)
│   │   └── connectors/          # S3 connector config reference
│   ├── snowflake/               # Native Snowflake objects
│   │   ├── stages.sql           # External S3 stages + file formats
│   │   ├── streams.sql          # CDC streams + TPCH_LANDING tables
│   │   └── tasks.sql            # Task DAG: MERGE → LOAD → REFRESH
│   ├── snowpark/                # Complex transforms as stored procedures
│   └── config/                  # Pipeline config YAML
│
├── dbt/                         # ── DataOps: Transform layer ──
│   ├── models/staging/          # Source-aligned views (1:1 with raw tables)
│   ├── models/intermediate/     # Ephemeral joins (never queried directly)
│   ├── models/marts/            # Incremental fact tables (Cortex Agent + BI)
│   ├── snapshots/               # Type-2 SCD on customers
│   ├── macros/                  # Schema naming, Snowflake-specific helpers
│   ├── tests/generic/           # Custom reusable data quality tests
│   └── profiles.yml.example     # dbt profile template
│
├── custom-ml-models/            # ── MLOps: Custom model lifecycle ──
│   ├── OPERATING_MODEL.md       # Lifecycle stages, roles, gates, control policies
│   ├── lifecycle/checklist.md   # Per-model stage-by-stage delivery checklist
│   ├── environments/            # dev.yml / staging.yml / prod.yml — SLO thresholds
│   ├── snowflake/sql/           # Foundation SQL: registry, lineage, monitoring
│   ├── templates/               # model_spec_template.yml + model_card_template.md
│   ├── runbooks/                # Release and incident/rollback procedures
│   └── examples/
│       ├── churn-risk-v1/       # Medium-risk worked example
│       └── fraud-risk-v1/       # High-risk, dual-approval worked example
│
├── agent/                       # ── AgentOps: Cortex Agent lifecycle ──
│   ├── deploy_all.py            # Deploy one or all agents
│   ├── run_evals.py             # Shared eval runner — works for any agent
│   └── agents/
│       └── tpch-analyst/        # One folder per agent
│           ├── agent.yml        # Identity: name, fqn, database, schema
│           ├── specs/v1/        # Versioned spec + metadata/changelog
│           ├── prompts/         # orchestration.md + response.md
│           ├── evals/           # eval_config.yaml, ground_truth.json, results/
│           └── monitoring/      # usage_queries.sql + alert_policy.yml
│
├── streamlit/                   # ── Dashboards: Multi-app Streamlit in Snowflake ──
│   ├── deploy_all.py            # Deploy one or all apps via Snowflake CLI
│   ├── shared/utils.py          # Shared session helper + formatting functions
│   └── apps/
│       ├── data-platform/       # Customer order KPI dashboard
│       └── ml-monitor/          # ML model health and deployment tracker
│
├── scripts/                     # Project automation scripts
│   ├── deploy_agent.py          # Build + emit CREATE AGENT SQL
│   ├── validate_agent_spec.py   # Validate agent spec schema
│   └── check_naming.py          # Enforce UPPER_SNAKE_CASE convention
│
└── .github/workflows/
    ├── validate.yml             # PR gate: analysis, dry-runs, syntax, security
    └── deploy.yml               # Release pipeline: DEV clone or PROD deploy
```

---

## DataOps

DataOps covers all infrastructure management, data ingestion, and transformations in this account.

### Declarative Infrastructure (DCM)

Snowflake objects are managed as code in `sources/definitions/` using `DEFINE` statements. DCM computes a diff and applies only what changed.

| DCM Target | Database | Used for |
|------------|----------|---------|
| `DEV` | `SANDBOX` | Local development |
| `CI` | `SANDBOX_<BRANCH>` | Branch pipeline (zero-copy clone, auto-cleaned) |
| `PROD` | `SANDBOX` | Production — auto-deployed on merge to `main` |

```bash
# Preview changes before applying
snow dcm plan --target DEV -c default

# Apply to dev
snow dcm deploy --target DEV -c default --alias "my-change"
```

### Ingestion Pipeline

Data flows from S3 through Snowflake Openflow into landing tables, then through a native Task DAG into production tables.

```
S3 Bucket
    │
    ▼
[Snowflake Openflow — SPCS/NiFi runtime]
  ListS3 → FetchS3 → ConvertRecord → PutSnowflakeStreaming
                                    → TPCH_LANDING.{CUSTOMERS,ORDERS}_RAW
  [failure] → RetryFlowFile (3×) → DLQ table
    │
    ▼  (Streams on landing tables trigger automatically)
[Snowflake Task DAG]
  MERGE_CUSTOMERS + LOAD_ORDERS  (parallel, stream-guarded)
        → REFRESH_SUMMARY
    │
    ▼
SANDBOX.TPCH.{CUSTOMERS, ORDERS}
```

For full setup instructions see [`ingestion/README.md`](ingestion/README.md).

### dbt Transform Layer

```
CUSTOMERS + ORDERS (sources)
    → stg_customers + stg_orders    (staging: views)
    → int_customer_orders           (intermediate: ephemeral)
    → fct_customer_orders           (mart: incremental MERGE, clustered)
         ├── Cortex Agent (semantic view)
         └── Streamlit dashboards
```

```bash
cd dbt && dbt deps && dbt run && dbt test
```

For the full model reference see [`dbt/README.md`](dbt/README.md).

---

## MLOps

`custom-ml-models/` is the production-grade lifecycle directory for custom ML models deployed in Snowflake. It covers the full journey from intake to retirement.

### Lifecycle Stages

```
Intake → Build → Qualify → Register → Deploy → Monitor → Retrain → Retire
```

Each stage has defined gates, approvals, and evidence requirements in [`custom-ml-models/OPERATING_MODEL.md`](custom-ml-models/OPERATING_MODEL.md).

### Snowflake MLOps Foundation

Three SQL scripts establish the MLOps schema in `ML_{ENV}.MLOPS`:

| Script | Objects created |
|--------|----------------|
| `001_setup_mlops_foundation.sql` | `MODEL_REGISTRY`, `MODEL_DEPLOYMENT_EVENTS` |
| `002_model_registry_and_lineage.sql` | `MODEL_LINEAGE`, `MODEL_APPROVALS`, `V_ACTIVE_MODELS` |
| `003_monitoring_views_and_alerts.sql` | `MODEL_PREDICTION_LOG`, `V_MODEL_HEALTH_DAILY` |

```bash
# Apply foundation (one-time per environment)
snow sql -f custom-ml-models/snowflake/sql/001_setup_mlops_foundation.sql -c default
snow sql -f custom-ml-models/snowflake/sql/002_model_registry_and_lineage.sql -c default
snow sql -f custom-ml-models/snowflake/sql/003_monitoring_views_and_alerts.sql -c default
```

CI deploys these automatically via the `deploy-ml-models` job on every push to `main`.

### Risk Tiers

| Tier | Dual approval in prod | Human-in-the-loop | Canary traffic |
|------|----------------------|-------------------|----------------|
| `low` | No | No | 10% |
| `medium` | No | Recommended | 10% |
| `high` | Yes (2 reviewers) | Required | 5% |

### Adding a New Model

```bash
# 1. Create model folder from templates
mkdir -p custom-ml-models/my-model-v1/snowflake/sql
cp custom-ml-models/templates/model_spec_template.yml  custom-ml-models/my-model-v1/model_spec.yml
cp custom-ml-models/templates/model_card_template.md   custom-ml-models/my-model-v1/model_card.md

# 2. Fill in spec and card, then validate locally
# spec must pass validate-ml-models in CI before PR merge

# 3. Register version in Snowflake after training
snow sql -f custom-ml-models/my-model-v1/snowflake/sql/001_register_model.sql -c default
```

See the worked examples in [`custom-ml-models/examples/`](custom-ml-models/examples/) — `churn-risk-v1` (medium-risk) and `fraud-risk-v1` (high-risk, dual-control).

For the full developer guide see [`custom-ml-models/README.md`](custom-ml-models/README.md).

---

## AgentOps

`agent/` owns the complete operational lifecycle of the `TPCH_ANALYST` Cortex Agent — the AI-powered data analyst scoped to `SANDBOX.TPCH`.

Each agent lives in `agent/agents/<name>/` with its own spec, prompts, evals, and monitoring. The folder structure mirrors `streamlit/apps/` — adding a new agent is just adding a new subfolder.

### Deployed Agents

| Agent folder | Snowflake FQN | Description |
|-------------|--------------|-------------|
| `tpch-analyst` | `SANDBOX.TPCH.TPCH_ANALYST` | Natural-language analyst for customer and order data |

### Deploying Agents

```bash
# Deploy all agents
python agent/deploy_all.py -c default

# Deploy a single agent
python agent/deploy_all.py -c default --agent tpch-analyst

# Dry-run
python agent/deploy_all.py --dry-run
```

### Running Evaluations

```bash
# Run evals for all agents
python agent/run_evals.py --all

# Run evals for a specific agent
python agent/run_evals.py --agent tpch-analyst

# Dry-run (validates config + ground truth without Snowflake calls)
python agent/run_evals.py --agent tpch-analyst --dry-run
```

### Eval Pass Thresholds (per agent, in `evals/eval_config.yaml`)

| Threshold | Value |
|-----------|-------|
| Overall weighted score | ≥ 0.80 |
| Per-question minimum | ≥ 0.60 |
| Tool call accuracy | 1.00 |

### Promoting a New Spec Version

1. Copy `agents/<name>/specs/v1/` → `v2/`, modify `agent_spec.json`.
2. Set `status: draft` in `metadata.yml` and add a changelog entry.
3. Run `python agent/deploy_all.py --dry-run --agent <name>` locally.
4. Open a PR — CI validates all agents automatically.
5. After merge, CI deploys all agents.

For the full developer guide see [`agent/README.md`](agent/README.md).

---

## Dashboards (Streamlit in Snowflake)

`streamlit/apps/` hosts multiple independently deployable SiS applications backed by a shared utilities layer.

| App | Snowflake name | Description |
|-----|---------------|-------------|
| `data-platform` | `SANDBOX.TPCH.DATA_PLATFORM_APP` | Customer order KPIs — total revenue, orders, top customers |
| `ml-monitor` | `SANDBOX.TPCH.ML_MONITOR_APP` | Active models, 7-day health metrics, deployment events |

```bash
# Deploy all apps
python streamlit/deploy_all.py -c default

# Deploy a single app
python streamlit/deploy_all.py -c default --app data-platform

# Add a new app: drop a folder in streamlit/apps/ with main.py,
# snowflake.yml, and environment.yml — deploy_all.py discovers it automatically.
```

For the full developer guide see [`streamlit/README.md`](streamlit/README.md).

---

## CI/CD Pipeline

### PR Validation (`validate.yml`)

Triggers on every pull request to `main`. All jobs run in parallel.

| Job | Pillar | What it validates |
|-----|--------|------------------|
| `validate-dcm` | DataOps | DCM analyze + plan dry-run against DEV target |
| `validate-ingestion` | DataOps | Openflow flow syntax + dry-run config check |
| `validate-dbt` | DataOps | `dbt compile`, `dbt parse` |
| `validate-ml-models` | MLOps | Model spec YAML fields, template syntax, SQL script presence |
| `validate-agent` | AgentOps | Spec schema validation, deploy dry-run, eval dry-run |
| `validate-streamlit` | Dashboards | AST syntax on all `apps/*/main.py`, required file presence |
| `lint-naming` | All | UPPER_SNAKE_CASE enforcement on DCM definitions |
| `security-scan` | All | Bandit (Python security) + Gitleaks (secret detection) |

### Deploy (`deploy.yml`)

| Trigger | Branch | Target |
|---------|--------|--------|
| Auto — push to `main` | `main` only | Always **PROD** |
| Manual — `workflow_dispatch` | Any branch | **DEV** (default) or **PROD** |

> Guard rail: dispatching `PROD` from any non-`main` branch fails immediately. Merge to `main` first.

#### Ordered Pipeline

```
guard
 └── clone-db          (DEV only — zero-copy clone: SANDBOX → SANDBOX_<BRANCH>)
       └── deploy-dcm  (schema objects)
             ├── deploy-ml-models   (MLOps SQL foundation: 001 → 002 → 003)
             └── deploy-ingestion   (stages, streams, tasks, Openflow flows, Snowpark)
                   └── deploy-dbt   (dbt run + test + snapshot)
                         ├── deploy-streamlit  (all apps via deploy_all.py)
                         └── deploy-agent
                               └── run-agent-evals  (upload artifact; skippable)
                                     └── cleanup-clone  (DEV: drop clone — always runs)
```

#### Branch Clone Database (DEV only)

Every DEV deploy creates a Snowflake **zero-copy clone** of `SANDBOX`. The clone name is derived from the branch name:

```
branch:  feature/my-model
clone:   SANDBOX_FEATURE_MY_MODEL
```

All components deploy into the clone — production is never touched. The clone is auto-dropped at pipeline end unless `keep_clone = true`.

```bash
# Inspect a retained clone
snow sql -q "SELECT * FROM SANDBOX_FEATURE_MY_MODEL.TPCH_DEV.FCT_CUSTOMER_ORDERS LIMIT 10;" -c dev

# Drop manually
snow sql -q "DROP DATABASE IF EXISTS SANDBOX_FEATURE_MY_MODEL;" -c dev
```

#### Environment Matrix

| Setting | DEV | PROD |
|---------|-----|------|
| Snowflake database | `SANDBOX_<BRANCH>` (clone) | `SANDBOX` |
| ML database | `ML_DEV` | `ML_PROD` |
| DCM target | `CI` (patched to clone) | `PROD` |
| dbt schema | `TPCH_DEV` | `TPCH` |
| Source freshness failure | warn only | blocks pipeline |
| Clone cleanup | auto-dropped | n/a |

#### Manual Run Options (`workflow_dispatch`)

| Input | Options | Default | Description |
|-------|---------|---------|-------------|
| `environment` | `DEV` / `PROD` | `DEV` | Target environment |
| `skip_evals` | `true` / `false` | `false` | Skip agent eval suite for faster iteration |
| `keep_clone` | `true` / `false` | `false` | Retain branch clone DB for post-deploy inspection |

---

## Required GitHub Secrets

Set in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Description |
|--------|-------------|
| `SNOWFLAKE_PAT` | Snowflake Programmatic Access Token — rotate in Snowsight after each use |
| `OPENFLOW_RUNTIME_URL` | Openflow SPCS runtime URL (available after ingestion one-time setup) |
| `S3_BUCKET` | Name of the S3 bucket hosting source CSV files |

---

## Folder READMEs

Each directory has a developer-focused README with quickstart commands, structure reference, and CI/CD integration notes.

| Folder | README | Covers |
|--------|--------|--------|
| `sources/` | [`sources/README.md`](sources/README.md) | DCM `DEFINE` syntax, object reference, change workflow |
| `ingestion/` | [`ingestion/README.md`](ingestion/README.md) | Openflow setup, Task DAG, Snowpark deployment |
| `dbt/` | [`dbt/README.md`](dbt/README.md) | Model layers, packages, lineage, dbt commands |
| `custom-ml-models/` | [`custom-ml-models/README.md`](custom-ml-models/README.md) | Full lifecycle quickstart, risk tiers, monitoring queries |
| `agent/` | [`agent/README.md`](agent/README.md) | Spec versioning, prompts, eval suite, monitoring |
| `streamlit/` | [`streamlit/README.md`](streamlit/README.md) | Multi-app layout, local dev, adding pages and new apps |
| `scripts/` | [`scripts/README.md`](scripts/README.md) | Per-script usage reference, pre-PR checklist |
