# snowflake-project

Enterprise-grade Snowflake data platform — DCM, Cortex Agent lifecycle, Openflow ingestion pipeline, and dbt transforms.

## Snowflake Connection

| Setting | Value |
|---------|-------|
| Account | `xna38553.east-us-2.azure` |
| Full host | `xna38553.east-us-2.azure.snowflakecomputing.com` |
| User | `MCP_SERVICE_USER` |
| Auth | Programmatic Access Token (PAT) |
| Database | `SANDBOX` |
| Schema | `TPCH` / `TPCH_LANDING` |
| Warehouse | `ANALYTICS_WH` |
| Role | `SYSADMIN` |

### Local Setup

```bash
# 1. Copy the connection template
cp config.toml.example config.toml

# 2. Paste your PAT into config.toml — NEVER commit this file (it is gitignored)
#    Generate/rotate PATs in Snowsight: Admin → Security → Programmatic Access Tokens

# 3. Verify the connection
snow connection test -c default
```

---

## Repository Layout

```
snowflake-project/
├── config.toml.example      # Connection template (copy → config.toml, fill PAT)
├── manifest.yml             # DCM project config (DEV / PROD targets)
├── sources/                 # DCM declarative object definitions
│   └── definitions/
│       ├── infrastructure.sql  # Warehouse
│       ├── tables.sql          # CUSTOMERS, ORDERS
│       ├── views.sql           # CUSTOMER_ORDER_SUMMARY
│       └── access.sql          # Roles + grants
├── agent/                   # Cortex Agent — enterprise lifecycle
│   ├── specs/               # Versioned agent specs
│   │   └── v1/              # agent_spec.json + metadata.yml
│   ├── evals/               # LLM-as-judge evaluation suite
│   │   ├── eval_config.yaml
│   │   ├── ground_truth.json
│   │   ├── run_evals.py
│   │   └── results/         # Eval run outputs (gitignored)
│   ├── prompts/             # Versioned prompt files
│   │   ├── orchestration.md
│   │   └── response.md
│   ├── monitoring/          # Operational observability
│   │   ├── usage_queries.sql
│   │   └── alert_policy.yml
│   ├── agent_spec.json      # Current canonical spec
│   └── instructions.md      # Legacy (superseded by prompts/)
├── ingestion/               # Data ingestion pipeline
│   ├── openflow/            # Snowflake Openflow (NiFi-based, SPCS-hosted)
│   │   ├── setup/           # Compute pool, roles, EAIs (run once by admin)
│   │   ├── flows/           # nipyapi flow definitions (Python)
│   │   └── connectors/      # S3 connector parameter reference
│   ├── snowflake/           # Native Snowflake objects
│   │   ├── stages.sql       # External S3 stages + file formats
│   │   ├── streams.sql      # CDC streams + landing tables
│   │   └── tasks.sql        # Snowflake Task DAG (post-Openflow processing)
│   ├── snowpark/            # Complex transforms as stored procedures
│   └── config/              # Pipeline configuration YAML
├── dbt/                     # dbt transform project
│   ├── models/staging/      # Source-aligned views
│   ├── models/intermediate/ # Ephemeral joins
│   ├── models/marts/        # Incremental fact tables (Cortex Agent + BI)
│   ├── snapshots/           # Type-2 SCD snapshots
│   ├── macros/              # Schema naming, Snowflake utils
│   ├── tests/generic/       # Custom generic tests
│   └── profiles.yml.example # dbt profile template
├── streamlit/               # Streamlit in Snowflake dashboard
├── scripts/                 # Deploy + validate scripts
└── .github/workflows/       # CI/CD
    ├── validate.yml          # PR checks (auto on every PR → main)
    └── deploy.yml            # Deploy pipeline (auto on main → PROD, manual on any branch → DEV/PROD)
```

---

## Component Overview

### DCM (Declarative Change Management)

Manages Snowflake infrastructure objects declaratively — warehouse, tables, views, roles/grants.
Supports three targets in `manifest.yml` with Jinja templating (`env_suffix`, `wh_size`):

| Target | Database | Used by |
|--------|----------|---------|
| `DEV` | `SANDBOX` | Local development |
| `CI` | `SANDBOX_<BRANCH>` | Branch pipeline (placeholder `SANDBOX_CI` replaced by `sed` at runtime) |
| `PROD` | `SANDBOX` | Main branch auto-deploy |

```bash
# Local dev
snow dcm plan --target DEV -c dev
snow dcm deploy --target DEV -c dev --alias "local-test"

# Production (CI handles this automatically on merge to main)
snow dcm deploy --target PROD -c prod --alias "gh-<sha>"
```

---

### Cortex Agent — Enterprise Lifecycle

Agent: `SANDBOX.TPCH.TPCH_ANALYST`

| Component | Path | Purpose |
|-----------|------|---------|
| Spec versioning | `agent/specs/v1/` | Immutable snapshots; `metadata.yml` tracks changelog and status |
| Evals | `agent/evals/` | Ground-truth Q&A pairs scored by `SNOWFLAKE.CORTEX.AI_JUDGE` |
| Prompts | `agent/prompts/` | Versioned orchestration + response formatting prompts |
| Monitoring | `agent/monitoring/` | Usage SQL (invocations, latency, credits) + Snowflake Alert DDL |

```bash
# Deploy agent (picks up prompts/ automatically)
python scripts/deploy_agent.py | snow sql -c prod --stdin

# Deploy a specific versioned spec
python scripts/deploy_agent.py --spec-version v2 | snow sql -c prod --stdin

# Run evaluations (set SNOWFLAKE_PAT env var first)
python agent/evals/run_evals.py
python agent/evals/run_evals.py --question-id GT-001
python agent/evals/run_evals.py --category ranking
python agent/evals/run_evals.py --dry-run
```

#### Promoting a new agent version

1. Create `agent/specs/vN/agent_spec.json` + `metadata.yml`
2. Run `python agent/evals/run_evals.py --dry-run` to validate
3. Open a PR — CI runs the full eval dry-run automatically
4. After merge, CI deploys with `--spec-version vN`

---

### Ingestion Pipeline (Snowflake Openflow + Task DAG)

**Snowflake Openflow** is Snowflake's native integration service built on Apache NiFi,
running inside Snowpark Container Services (SPCS). It is managed entirely within Snowflake —
no external orchestrator required.

```
S3 Bucket
    │
    ▼
[Snowflake Openflow — SPCS runtime]
  ListS3 → FetchS3Object → ConvertRecord → UpdateRecord
        → PutSnowflakeStreaming → TPCH_LANDING.{CUSTOMERS,ORDERS}_RAW
  [failure] → RetryFlowFile (3 retries) → DLQ table
    │
    ▼  (Streams pick up new rows automatically)
[Snowflake Task DAG]
  MERGE_CUSTOMERS + LOAD_ORDERS (parallel, stream-guarded)
        → REFRESH_SUMMARY
    │
    ▼
SANDBOX.TPCH.{CUSTOMERS, ORDERS} → dbt mart → fct_customer_orders
```

#### One-time admin setup

```bash
# 1. Compute pool + roles + EAIs (run as ACCOUNTADMIN)
snow sql -f ingestion/openflow/setup/01_compute_pool.sql -c prod
snow sql -f ingestion/openflow/setup/02_roles_and_grants.sql -c prod
snow sql -f ingestion/openflow/setup/03_external_access.sql -c prod

# 2. Create Openflow deployment + runtime in Snowsight:
#    Data → Openflow → Create Deployment → Openflow - Snowflake
#    Compute pool: TPCH_OPENFLOW_POOL | Runtime role: DATA_PLATFORM_OPENFLOW

# 3. Deploy landing tables, streams, and task DAG
snow sql -f ingestion/snowflake/stages.sql  -c prod
snow sql -f ingestion/snowflake/streams.sql -c prod
snow sql -f ingestion/snowflake/tasks.sql   -c prod

# 4. Resume the task DAG (resume leaf tasks first, root last)
snow sql -q "ALTER TASK SANDBOX.TPCH.REFRESH_SUMMARY_TASK RESUME;"   -c prod
snow sql -q "ALTER TASK SANDBOX.TPCH.LOAD_ORDERS_TASK RESUME;"       -c prod
snow sql -q "ALTER TASK SANDBOX.TPCH.MERGE_CUSTOMERS_TASK RESUME;"   -c prod
snow sql -q "ALTER TASK SANDBOX.TPCH.PIPELINE_ROOT_TASK RESUME;"     -c prod
```

#### Deploy Openflow flows (programmatic via nipyapi)

```bash
pip install -r ingestion/openflow/requirements.txt

export OPENFLOW_RUNTIME_URL=https://<runtime-id>.snowflakecomputing.com/nifi
export S3_BUCKET=your-data-bucket

python ingestion/openflow/flows/deploy_all_flows.py
python ingestion/openflow/flows/deploy_all_flows.py --dry-run  # inspect flow config
```

#### Deploy Snowpark stored procedures

```bash
export SNOWFLAKE_PAT=<your-pat>
python ingestion/snowpark/transforms.py
```

---

### dbt — Transform Layer

| Package | Purpose |
|---------|---------|
| `dbt_utils` | `generate_surrogate_key`, `date_spine`, cross-db macros |
| `dbt_expectations` | Range checks, regex tests, row count assertions |
| `audit_helper` | Row count and value comparison across runs |
| `codegen` | Auto-generate source YAML from Snowflake schema |
| `elementary` | Data observability — anomaly detection, schema changes |

```bash
# Setup (copy profile template and set PAT)
cp dbt/profiles.yml.example ~/.dbt/profiles.yml
export SNOWFLAKE_PAT=<your-pat>

cd dbt
dbt deps             # Install packages
dbt debug            # Test connection
dbt source freshness # Check source data recency
dbt run              # Run all models
dbt test             # Run all tests
dbt snapshot         # Run Type-2 SCD snapshots
```

**Data lineage:**
```
CUSTOMERS (source) + ORDERS (source)
    → stg_customers + stg_orders          (staging: views)
    → int_customer_orders                  (intermediate: ephemeral)
    → fct_customer_orders                  (mart: incremental MERGE, clustered)
         ├── Cortex Agent (semantic view)
         └── Streamlit dashboard
```

---

## CI/CD Pipeline

### PR Validation (`.github/workflows/validate.yml`)

Triggers automatically on every pull request targeting `main`.

| Job | What it checks |
|-----|---------------|
| `validate-dcm` | DCM analyze + plan against DEV target |
| `validate-agent` | Spec JSON validation, deploy dry-run, eval dry-run |
| `validate-dbt` | `dbt deps`, `dbt compile`, `dbt parse` |
| `validate-ingestion` | Openflow flow Python syntax + dry-run config check |
| `lint-naming` | UPPER_SNAKE_CASE on all DCM definition files |
| `validate-streamlit` | Python AST syntax check |
| `security-scan` | Bandit (Python) + Gitleaks (secrets) |

### Deploy (`.github/workflows/deploy.yml`)

#### Triggers

| How | When | Target |
|-----|------|--------|
| Automatic | Push to `main` | Always **PROD** |
| Manual (`workflow_dispatch`) | Any branch, any time | **DEV** (default) or **PROD** |

#### Running a test deploy on your branch

```bash
# 1. Push your branch first
git push origin feature/advanced_devops
```

Then in GitHub:

1. **Actions → Deploy → Run workflow**
2. Branch: `feature/advanced_devops`
3. Environment: `DEV` (default — never touches production)
4. Skip evals: `false` (or `true` for a faster first run)
5. Keep clone: `true` to inspect the branch database after the pipeline
6. **Run workflow**

> **Guard rail:** dispatching to `PROD` from any non-`main` branch fails immediately at the `guard` job. Merge to `main` first for production deploys.

#### Branch clone database (DEV only)

Every DEV deploy automatically creates a **Snowflake zero-copy clone** of `SANDBOX`. The clone name is derived from the branch name — slashes, hyphens, and dots become underscores, uppercased, truncated to 30 chars:

```
Branch: feature/advanced_devops
Clone:  SANDBOX_FEATURE_ADVANCED_DEVOPS
```

All objects — DCM schema changes, ingestion SQL, dbt models, agent evals — deploy into the clone. Production (`SANDBOX`) is never touched. The clone is automatically dropped at the end of the pipeline unless `keep_clone = true`.

To inspect a retained clone locally:
```bash
# Browse the clone
snow sql -q "SHOW SCHEMAS IN DATABASE SANDBOX_FEATURE_ADVANCED_DEVOPS;" -c dev
snow sql -q "SELECT * FROM SANDBOX_FEATURE_ADVANCED_DEVOPS.TPCH_DEV.FCT_CUSTOMER_ORDERS LIMIT 10;" -c dev

# Drop manually when done
snow sql -q "DROP DATABASE IF EXISTS SANDBOX_FEATURE_ADVANCED_DEVOPS;" -c dev
```

#### What each environment targets

| Setting | DEV | PROD |
|---------|-----|------|
| Database | `SANDBOX_<BRANCH>` (clone) | `SANDBOX` |
| DCM target | `CI` (patched to clone) | `PROD` |
| dbt database | clone DB | `SANDBOX` |
| dbt schema | `TPCH_DEV` | `TPCH` |
| Source freshness failure | warn only | blocks pipeline |
| Clone cleanup | auto-dropped (unless `keep_clone=true`) | n/a |

#### Ordered pipeline

```
guard
  └── clone-db  (DEV only: CREATE OR REPLACE DATABASE SANDBOX_<BRANCH> CLONE SANDBOX)
        └── deploy-dcm  (CI target patched to clone / PROD target for main)
              └── deploy-ingestion  (SQL repointed to clone on DEV)
                      └── deploy-dbt  (dbt database = clone on DEV)
                              ├── deploy-streamlit
                              └── deploy-agent
                                        └── run-agent-evals  (artifact uploaded, skippable)
                                                  └── cleanup-clone  (DEV: drop clone, always runs)
```

---

## Required GitHub Secrets

Set these in **GitHub repo → Settings → Secrets and variables → Actions**:

| Secret | Value / Description |
|--------|---------------------|
| `SNOWFLAKE_PAT` | Snowflake Programmatic Access Token — rotate in Snowsight after each use |
| `OPENFLOW_RUNTIME_URL` | Openflow SPCS runtime URL (available after Step 2 of ingestion setup) |
| `S3_BUCKET` | Name of the S3 bucket hosting source CSV files |

> Account (`xna38553.east-us-2.azure`) and user (`MCP_SERVICE_USER`) are hardcoded in the
> workflow files as non-secret configuration. Only the PAT is a secret.

## `workflow_dispatch` Inputs (manual runs)

| Input | Options | Default | Description |
|-------|---------|---------|-------------|
| `environment` | `DEV` / `PROD` | `DEV` | Target environment. PROD blocked on non-main branches. |
| `skip_evals` | `true` / `false` | `false` | Skip the agent evaluation suite for faster iteration. |
| `keep_clone` | `true` / `false` | `false` | Retain the branch clone DB after the pipeline for inspection. |
