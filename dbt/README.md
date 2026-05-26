# dbt — TPCH Data Platform

dbt project for the `SANDBOX.TPCH` data platform. Transforms raw ingested data
into clean staging models and business-ready mart tables consumable by the
Cortex Agent, Streamlit dashboard, and BI tools.

## Project Structure

```
dbt/
├── dbt_project.yml              # Project config, model materializations, vars
├── packages.yml                 # dbt package dependencies
├── profiles.yml.example         # Template — copy to ~/.dbt/profiles.yml
├── models/
│   ├── staging/                 # Source-aligned views (1:1 with raw tables)
│   │   ├── _sources.yml         # Source definitions + freshness + tests
│   │   ├── _staging.yml         # Staging model tests
│   │   ├── stg_customers.sql
│   │   └── stg_orders.sql
│   ├── intermediate/            # Ephemeral joins — never queried directly
│   │   └── int_customer_orders.sql
│   └── marts/                   # Business-ready incremental tables
│       ├── _marts.yml           # Column docs + tests
│       └── fct_customer_orders.sql
├── snapshots/
│   └── customers_snapshot.sql   # Type-2 SCD on customers
├── tests/
│   └── generic/
│       └── is_valid_email.sql   # Custom generic test
├── macros/
│   ├── generate_schema_name.sql # Schema naming override (no prefix in prod)
│   └── snowflake_utils.sql      # Snowflake helper macros
├── analyses/
│   └── customer_segment_report.sql
└── seeds/                       # Reference data (add CSVs here)
```

## Packages

| Package | Purpose |
|---------|---------|
| `dbt_utils` | `generate_surrogate_key`, `date_spine`, cross-db macros |
| `dbt_expectations` | `expect_column_values_to_be_between`, regex tests |
| `audit_helper` | Compare row counts across runs, schema diffing |
| `codegen` | Auto-generate source YAML from Snowflake schema |
| `elementary` | Data observability, anomaly detection, test results tracking |

## Quickstart

```bash
# Install dbt-snowflake
pip install dbt-snowflake

# Copy and configure your profile
cp dbt/profiles.yml.example ~/.dbt/profiles.yml
# Edit ~/.dbt/profiles.yml with your Snowflake credentials

# Install packages
cd dbt
dbt deps

# Test connection
dbt debug

# Run source freshness checks
dbt source freshness

# Run all models
dbt run

# Run tests
dbt test

# Run snapshots
dbt snapshot

# Run specific layer
dbt run --select staging
dbt run --select marts
```

## Data Lineage

```
SANDBOX.TPCH.CUSTOMERS (source)
SANDBOX.TPCH.ORDERS    (source)
        │
        ▼
   stg_customers   stg_orders      (staging: views)
        │               │
        └───────┬───────┘
                ▼
     int_customer_orders            (intermediate: ephemeral)
                │
                ▼
     fct_customer_orders            (mart: incremental table)
                │
        ┌───────┴────────────────────┐
        ▼                            ▼
  Cortex Agent              Streamlit Dashboard
  (semantic view)
```

## CI/CD

dbt runs are integrated into the GitHub Actions pipeline:
- **PR validation**: `dbt compile`, `dbt test --select state:modified+`
- **Main branch deploy**: `dbt run --target prod`, `dbt test`, `dbt snapshot`

## Snowflake Best Practices Applied

| Practice | Implementation |
|----------|---------------|
| Incremental MERGE | `fct_customer_orders` uses `incremental_strategy = 'merge'` with `unique_key` |
| Clustering | Mart table clustered by `last_order_date` for time-range scan efficiency |
| Schema isolation | `generate_schema_name` macro prevents schema name collisions across targets |
| Column grants | `DATA_READER` role granted SELECT on marts via `+grants` in `dbt_project.yml` |
| Type-2 SCD | `customers_snapshot` captures historical changes |
| Source freshness | Freshness thresholds defined in `_sources.yml` |
| Surrogate keys | `dbt_utils.generate_surrogate_key` for stable downstream joins |
