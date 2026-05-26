# Ingestion

End-to-end data ingestion pipeline for `SANDBOX.TPCH` using **Snowflake Openflow** (the Snowflake-native, NiFi-based integration service) for orchestration, and Snowflake-native Streams and Tasks for in-Snowflake processing.

## Architecture

```
S3 Bucket (source files)
       │
       ▼
[Snowflake Openflow]  (SPCS-hosted NiFi runtime, visual canvas in Snowsight)
  ListS3 → FetchS3Object → ConvertRecord → UpdateRecord
        → PutSnowflakeStreaming → TPCH_LANDING.{CUSTOMERS,ORDERS}_RAW
  [failure] → RetryFlowFile (3 retries) → DLQ table on exhaustion
       │
       │  (Openflow writes trigger Streams automatically)
       ▼
  Snowflake Stream (CDC on landing tables)
       │
       ▼
  Snowflake Task DAG  (native orchestration, SYSTEM$STREAM_HAS_DATA guard)
  MERGE_CUSTOMERS + LOAD_ORDERS (parallel) → REFRESH_SUMMARY
       │
       ▼
  SANDBOX.TPCH.{CUSTOMERS, ORDERS}  →  fct_customer_orders (dbt mart)
```

## Directory Layout

```
ingestion/
├── openflow/
│   ├── setup/
│   │   ├── 01_compute_pool.sql          # SPCS compute pool for Openflow deployment
│   │   ├── 02_roles_and_grants.sql      # Least-privilege role + grants for runtime
│   │   └── 03_external_access.sql       # EAIs + network rules for S3 egress
│   ├── flows/
│   │   ├── customers_flow.py            # nipyapi: Customers S3→Snowflake flow
│   │   ├── orders_flow.py               # nipyapi: Orders S3→Snowflake flow
│   │   └── deploy_all_flows.py          # Deploy both flows in one command
│   ├── connectors/
│   │   └── s3_connector_config.yml      # S3 connector parameter reference
│   └── requirements.txt                 # nipyapi + Snowflake deps
├── snowflake/
│   ├── stages.sql                       # External S3 stages, file formats
│   ├── streams.sql                      # CDC streams + landing tables
│   └── tasks.sql                        # Snowflake Task DAG (post-Openflow processing)
├── snowpark/
│   └── transforms.py                    # Stored procedures for complex transforms
└── config/
    └── pipeline_config.yml              # Centralised pipeline configuration
```

## About Snowflake Openflow

Openflow is Snowflake's native integration service built on **Apache NiFi** (via the Datavolo acquisition). It runs inside **Snowpark Container Services (SPCS)** and is managed entirely within Snowflake — no external orchestrator needed.

| Feature | Detail |
|---------|--------|
| Architecture | Split-plane: Control plane (Snowsight canvas) + Data plane (SPCS) |
| Authentication | **Snowflake Managed Token** — auto-managed SPCS session token, no key-pairs |
| Deployment type | Openflow - Snowflake (SPCS), single deployment per account, multiple runtimes |
| Programmatic control | `nipyapi` Python library (Apache NiFi REST API client) |
| Retry + DLQ | NiFi `RetryFlowFile` processor + dead-letter queue table |
| Data format | CSV, JSON, Avro, Parquet — converted via `ConvertRecord` + `SplitRecord` |

## Quickstart

### Step 1 — Snowflake admin setup

```bash
# 1a. Create compute pool (run as ACCOUNTADMIN)
snow sql -f ingestion/openflow/setup/01_compute_pool.sql -c prod

# 1b. Create roles and grants
snow sql -f ingestion/openflow/setup/02_roles_and_grants.sql -c prod

# 1c. Create EAIs and network rules for S3 egress
snow sql -f ingestion/openflow/setup/03_external_access.sql -c prod
```

### Step 2 — Create Openflow deployment and runtime (Snowsight UI)

1. Open Snowsight → **Data** → **Openflow**
2. Click **Create Deployment** → choose **Openflow - Snowflake** (SPCS)
3. Select compute pool: `TPCH_OPENFLOW_POOL`
4. Create a **Runtime** named `TPCH_OPENFLOW_RUNTIME` with role `DATA_PLATFORM_OPENFLOW`
5. Note the runtime URL (e.g. `https://abc123.snowflakecomputing.com/nifi`)

### Step 3 — Deploy Snowflake landing tables, streams, and tasks

```bash
snow sql -f ingestion/snowflake/stages.sql -c prod
snow sql -f ingestion/snowflake/streams.sql -c prod
snow sql -f ingestion/snowflake/tasks.sql -c prod

# Resume the task DAG
snow sql -q "ALTER TASK SANDBOX.TPCH.REFRESH_SUMMARY_TASK RESUME;" -c prod
snow sql -q "ALTER TASK SANDBOX.TPCH.LOAD_ORDERS_TASK RESUME;" -c prod
snow sql -q "ALTER TASK SANDBOX.TPCH.MERGE_CUSTOMERS_TASK RESUME;" -c prod
snow sql -q "ALTER TASK SANDBOX.TPCH.PIPELINE_ROOT_TASK RESUME;" -c prod
```

### Step 4 — Deploy Openflow flows programmatically

```bash
pip install -r ingestion/openflow/requirements.txt

export OPENFLOW_RUNTIME_URL=https://your-runtime.snowflakecomputing.com/nifi
export S3_BUCKET=your-data-bucket

# Deploy and start both flows
python ingestion/openflow/flows/deploy_all_flows.py

# Or dry-run to inspect the flow config
python ingestion/openflow/flows/deploy_all_flows.py --dry-run
```

### Step 5 — Register Snowpark stored procedures

```bash
export SNOWFLAKE_ACCOUNT=...
export SNOWFLAKE_USER=...
export SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/key.p8
python ingestion/snowpark/transforms.py
```

## Snowflake Best Practices Applied

| Practice | Implementation |
|----------|---------------|
| Native orchestration | Snowflake Openflow (SPCS) — no external scheduler dependency |
| Managed auth | `SNOWFLAKE_MANAGED` token — no key-pairs or service user credentials |
| Least privilege | Dedicated `DATA_PLATFORM_OPENFLOW` role with minimal grants |
| EAI for egress | All external network access gated via External Access Integrations |
| Retry + DLQ | NiFi `RetryFlowFile` (3 retries) + dedicated DLQ Snowflake tables |
| CDC via Streams | Snowflake Streams on landing tables feed native Task DAG |
| Conditional tasks | `SYSTEM$STREAM_HAS_DATA` guards prevent empty runs |
| Code-as-config | Flows defined in Python (nipyapi) for version control and CI reproducibility |
