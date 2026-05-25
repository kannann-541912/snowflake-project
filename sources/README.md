# sources — Developer Guide

The `sources/` directory contains **DCM (Declarative Configuration Management)** definition files for all Snowflake infrastructure objects owned by this project. DCM treats Snowflake objects as code — changes here are applied to Snowflake via `snow dcm` commands, not manual SQL.

## Directory Layout

```
sources/
└── definitions/
    ├── tables.sql         # DEFINE TABLE — source tables (CUSTOMERS, ORDERS)
    ├── views.sql          # DEFINE VIEW — derived views (CUSTOMER_ORDER_SUMMARY)
    ├── access.sql         # DEFINE ROLE + GRANT — roles and privileges
    └── infrastructure.sql # DEFINE WAREHOUSE — compute resources
```

## How DCM Works

DCM definitions use `DEFINE` statements (not `CREATE`). DCM computes a diff between the declared state in these files and the live Snowflake environment, then applies only the changes needed.

```
DEFINE TABLE  →  creates or alters the table in Snowflake
DEFINE VIEW   →  creates or replaces the view
DEFINE ROLE + GRANT → manages role membership and privileges
DEFINE WAREHOUSE    → creates or resizes the warehouse
```

## Quickstart — Apply Changes Locally

```bash
pip install snowflake-cli

# Analyze — show what DCM sees as the current state
snow dcm raw-analyze --target DEV -c default

# Plan — show what changes would be made (dry-run, no writes)
snow dcm plan --target DEV -c default

# Deploy — apply the declared changes to Snowflake
snow dcm deploy --target DEV -c default --alias "my-change-$(date +%s)"
```

Replace `DEV` with `PROD` for production. Only CI deploys to `PROD` from `main`.

## Object Reference

### Tables (`definitions/tables.sql`)

| Object | Description |
|--------|-------------|
| `SANDBOX.TPCH.CUSTOMERS` | Customer master data — source for dbt staging and ingestion |
| `SANDBOX.TPCH.ORDERS` | Order transactions — `CHANGE_TRACKING = TRUE` for CDC via Streams |

### Views (`definitions/views.sql`)

| Object | Description |
|--------|-------------|
| `SANDBOX.TPCH.CUSTOMER_ORDER_SUMMARY` | Aggregated customer KPIs — queried directly by the Streamlit app |

### Access (`definitions/access.sql`)

| Object | Description |
|--------|-------------|
| `DATA_READER{{env_suffix}}` | Read-only role — SELECT on tables and views, USAGE on warehouse |

`{{env_suffix}}` is a DCM template variable resolved per target (empty in PROD, `_DEV` in DEV).

### Infrastructure (`definitions/infrastructure.sql`)

| Object | Description |
|--------|-------------|
| `ANALYTICS_WH{{env_suffix}}` | Shared warehouse — auto-suspend 60s, auto-resume, initially suspended |

`{{wh_size}}` is resolved per target environment (e.g. `X-SMALL` in DEV, `SMALL` in PROD).

## Making a Change

1. Edit the relevant `.sql` file in `definitions/`.
2. Run `snow dcm plan --target DEV -c default` to preview the diff.
3. Verify the plan looks correct — it shows which objects will be created, altered, or dropped.
4. Open a PR. `validate.yml` runs `dcm analyze` and `dcm plan` automatically.
5. After merge, `deploy.yml` applies changes via `dcm deploy`.

## Rules

- Never write raw `CREATE` or `ALTER` SQL here — always use `DEFINE` statements so DCM tracks ownership.
- Never apply changes directly to `PROD` outside of CI — all production changes must go through a PR and `deploy.yml`.
- If an object needs to be dropped, remove its `DEFINE` block and let DCM handle the drop in the plan step.
