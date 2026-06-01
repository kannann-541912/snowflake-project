# Category Intelligence Platform

A Snowflake-native Category Intelligence platform that empowers category managers with competitive pricing intelligence, promotion, ROI tracking, customer loyalty insights, and returns margin analysis — all accessible through a conversational AI agent and interactive Streamlit dashboard.

---

## Business Overview

### Problem Statement

Category managers spend hours manually tracking competitor prices, evaluating promotion effectiveness, identifying at-risk customers, and analyzing return patterns across hundreds of SKUs. Decisions are delayed, margins erode, and stockouts go undetected.

### Solution

The Category Intelligence Platform automates the entire analytics workflow:

1. **Competitor Price Ingestion** — Automated scraping of competitor prices via SerpAPI Google Shopping
2. **Medallion Data Pipeline** — Raw data flows through Bronze → Silver → Gold with automated quality checks
3. **AI-Powered Recommendations** — Cortex AI generates SKU-level action recommendations (reprice, replenish, promote, monitor)
4. **Conversational Agent** — Natural language interface for instant analytics without writing SQL
5. **Interactive Dashboard** — Streamlit app for visual exploration and one-click action execution

### Target Users

- **Category Managers** — Daily pricing decisions, promotion planning, assortment optimization
- **Merchandising Directors** — Category health monitoring, margin governance
- **Supply Chain Analysts** — Stock availability, replenishment triggers
- **Marketing Teams** — Promotion ROI, campaign performance tracking

### Key Metrics Tracked

| Domain | KPIs |
|--------|------|
| Pricing | Price gap %, competitive positioning, margin %, AI action recommendations |
| Promotions | ROAS, unit lift %, revenue lift %, performance status |
| Loyalty | Customer LTV, churn risk score, segment distribution, points redemption |
| Returns | Return rate %, margin erosion $, top return reasons, rationalization flags |
| Inventory | Stock levels, days until stockout, replenishment urgency |

---

## Snowflake Features Used

| Feature | How It's Used |
|---------|---------------|
| **Cortex Agents** | Natural language analytics agent with tool-calling (procedures + text-to-SQL) |
| **Cortex AI (LLM)** | `SNOWFLAKE.CORTEX.COMPLETE('mistral-large2')` for per-SKU action recommendations |
| **Semantic Views** | Maps 5 analytics views with facts, dimensions, and verified queries for the agent |
| **Dynamic Tables** | `GOLD_CATEGORY_PERFORMANCE_SUMMARY` auto-refreshes every 30 min from upstream |
| **Snowpark Python** | 4 stored procedures for ingestion, transformation, DQ validation, and Gold refresh |
| **External Access Integration** | Egress to SerpAPI for competitor price scraping |
| **Network Rules** | HOST_PORT egress rule allowing `serpapi.com` |
| **Secrets** | `GENERIC_STRING` secret for SerpAPI API key management |
| **Tasks (DAG)** | 4-task dependency chain for daily pipeline orchestration |
| **Streamlit in Snowflake** | Interactive dashboard running on SPCS with owner execution |
| **Change Tracking** | Enabled on Silver/Gold tables to support Dynamic Table refresh |
| **Transient Tables** | dbt snapshot table (SCD Type 2) for pricing history |
| **VARIANT columns** | JSON storage for SerpAPI responses and DQ failure samples |
| **DCM** | Declarative Configuration Management for infrastructure-as-code |
| **Object Tagging** | Privacy/semantic classification tags on PII columns (name, email) |
| **Data Quality Checks** | Custom 6-check DQ suite with pass/fail logging and sample capture |

---

## Streamlit Dashboard

### App Configuration

- **Name**: `CATEGORY_INTELLIGENCE_PLATFORM`
- **Warehouse**: `RETAIL_CATEGORY_ANALYTICS_WH`
- **Run Mode**: SPCS (Snowpark Container Services)
- **Main File**: `streamlit_app.py`

### Features

| Page/Section | Description |
|---|---|
| **Pricing Intelligence** | Table of all SKUs with competitor prices, margins, positioning status, and AI recommendations. Filter by category/brand. One-click reprice/replenish actions. |
| **Category Health** | KPI cards per category showing overpriced/underpriced counts, stock alerts, average margins, and inventory value. |
| **Promotion Performance** | Campaign table with ROAS, lift metrics, budget utilization, and performance classification. |
| **Customer Loyalty** | Member table with LTV, churn risk, segment, tenure, and recommended engagement actions. |
| **Returns Analysis** | SKU-level return rates, margin erosion, top reasons, and rationalization recommendations. |
| **AI Agent Chat** | Embedded conversational interface for natural language queries against all analytics views. |
| **Action Audit Trail** | Immutable log of all actions taken (reprice, replenish, monitor, escalate) with before/after state. |

### Deploy Streamlit App

```bash
cd streamlit
snow streamlit deploy --replace
```

---

## Data Pipeline Flow

### Ingestion (Bronze Layer)

```
┌──────────────────┐     ┌────────────────────┐       ┌────────────────────────┐
│   SerpAPI        │────▶│ INGEST_COMPETITOR_  │────▶│ BRONZE_COMPETITOR_     │
│ Google Shopping  │     │ PRICES_FROM_SERPAPI │      │ PRICE_RAW (480 rows)   │
└──────────────────┘     └────────────────────┘       └────────────────────────┘

┌──────────────────┐                                ┌──────────────────────────┐
│   CSV Upload     │───────────────────────────────▶│ BRONZE_SKU_MASTER_RAW    │
│ (RAW_DATA_STAGE) │                                │ (100 SKUs)               │
└──────────────────┘                                └──────────────────────────┘

Additional Bronze sources: Weekly Sales, Promotions, Loyalty Members, Transactions, Returns
```

### Transformation (Silver Layer)

**Procedure**: `TRANSFORM_BRONZE_TO_SILVER_PIPELINE()`

| Transform | Logic |
|---|---|
| SKU Master | Type-cast, validate prices, derive margins, compute stock status, flag DQ failures |
| Competitor Prices | Join with SKU master, compute price gaps, classify positioning, flag opportunities |
| Weekly Sales | Cleanse nulls, validate positive units, standardize brand/category casing |
| Promotions | Join promos + SKU assignments + SKU master, compute discount amounts |
| Returns | Join with SKU master, compute margin lost, calculate days-to-return |
| Loyalty | MERGE members + transactions, compute aggregates, identify top category/brand |

### Gold Layer (Analytics-Ready)

**Procedure**: `REFRESH_GOLD_LAYER_PIPELINE()`

| Gold Table | Refresh Logic |
|---|---|
| `GOLD_SKU_PRICING_INTELLIGENCE` | Joins Silver SKU + competitor aggregates, assigns primary competitor, computes stockout estimates |
| `GOLD_CATEGORY_PERFORMANCE_SUMMARY` | **Dynamic Table** — auto-refreshes every 30 min |
| `GOLD_WEEKLY_BRAND_SELL_THROUGH` | Aggregates Silver sales by brand/week for 13-week trend charts |
| `GOLD_PROMOTION_PERFORMANCE` | Compares promo-period vs baseline sales, computes ROAS and lift |
| `GOLD_RETURNS_MARGIN_ANALYSIS` | Aggregates returns per SKU, computes rates, assigns recommended actions |
| `GOLD_LOYALTY_CUSTOMER_INSIGHTS` | Computes LTV, churn risk (0-1), segments customers, recommends engagement |

**AI Enrichment**: After Gold refresh, Cortex AI generates per-SKU action recommendations for any SKU flagged for price review or replenishment.

### Refresh Cadence

| Component | Schedule |
|---|---|
| Daily pipeline (Bronze→Silver→DQ→Gold) | 6:00 AM UTC (CRON task) |
| Category Performance Summary | Every 30 minutes (Dynamic Table) |
| Competitor price ingestion | Manual trigger (preserves API credits) |
| dbt snapshot (SCD Type 2) | On-demand (`dbt snapshot`) |

---

## Cortex AI Agent Usage Guide

### Overview

The **Retail Category Analytics Agent** provides a natural language interface to all analytics data. It uses a semantic view to understand questions and routes them to the correct underlying data.

### Available Tools

| Tool | Type | Use Case |
|---|---|---|
| `query_pricing_data` | cortex_analyst_text_to_sql | Any data question across all 5 analytics views |
| `execute_sku_action` | procedure | Take action on a SKU (requires confirmation) |
| `get_category_health` | procedure | Category-level KPI summary |
| `get_pricing_alerts` | procedure | SKUs needing immediate price review |

### Sample Questions

**Pricing**: "Show me overpriced SKUs in the AUDIO category"
**Promotions**: "What's the ROAS of the best campaign?"
**Loyalty**: "Which customers are at high churn risk?"
**Returns**: "Which SKUs have the highest return rates?"
**Actions**: "Reprice SKU ELEC-SKU-0022 to match competitor" (requires confirmation)

### Routing Rules

| Question Topic | Routed To |
|---|---|
| Pricing, margins, competitors, stock | `PRICING_INTELLIGENCE_ANALYTICS_VIEW` |
| Promotions, campaigns, ROAS, lift | `PROMOTION_PERFORMANCE_ANALYTICS_VIEW` |
| Customers, churn, loyalty, LTV | `LOYALTY_CUSTOMER_ANALYTICS_VIEW` |
| Returns, refunds, margin lost | `RETURNS_MARGIN_ANALYTICS_VIEW` |
| Category-level summaries | `CATEGORY_PERFORMANCE_ANALYTICS_VIEW` |

---

## Project Structure

```
Category_Intelligence_Platform/
├── sources/definitions/          # DCM-managed Snowflake object definitions
│   ├── tables.sql                # DEFINE TABLE (Bronze/Silver/Gold, 24 tables)
│   ├── views.sql                 # DEFINE VIEW (STG/INT/Analytics, 15 views)
│   ├── dynamic_tables.sql        # DEFINE DYNAMIC TABLE (Gold category summary)
│   ├── infrastructure.sql        # DEFINE WAREHOUSE + SCHEMA
│   ├── access.sql                # DEFINE ROLE + GRANT statements
│   ├── procedures.sql            # SQL stored procedures (3)
│   ├── network.sql               # Network Rule + External Access Integration
│   └── secrets.sql               # Secrets (placeholder, no values in code)
│
├── ingestion/
│   ├── snowflake/
│   │   ├── stages.sql            # DEFINE STAGE (internal stages)
│   │   └── tasks.sql             # CREATE OR REPLACE TASK (DAG pipeline)
│   └── snowpark/
│       └── transforms.py         # Python/Snowpark procedures (4)
│
├── dbt/                          # dbt transformation layer
│   ├── dbt_project.yml
│   ├── packages.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── sources.yml
│   │   ├── staging/              # stg_* views (5 models)
│   │   ├── intermediate/         # int_* views (5 models)
│   │   └── marts/                # Analytics views (5 models)
│   ├── snapshots/                # SCD Type 2 snapshot
│   ├── analyses/                 # Ad-hoc analytical queries
│   ├── macros/
│   └── tests/generic/
│
├── agent/                        # Cortex Agent (AgentOps)
│   ├── deploy_all.py             # Shared: deploys all agents
│   ├── run_evals.py              # Shared: runs eval suites
│   └── agents/
│       └── retail-category-analytics/
│           ├── agent.yml         # Discovery anchor
│           ├── specs/v1/         # Versioned agent spec
│           ├── prompts/          # Orchestration + response prompts
│           ├── evals/            # Ground-truth eval suite (8 cases)
│           ├── monitoring/       # Alert policy + usage queries
│           └── semantic_view/    # Semantic view DDL
│
├── streamlit/                    # Streamlit dashboard app (SPCS)
│   ├── .streamlit/config.toml   # Streamlit theme/config
│   ├── snowflake.yml            # Snowflake app deployment config
│   ├── pyproject.toml           # Python dependencies
│   ├── streamlit_app.py         # Main application (135 KB)
│   ├── styles.py                # Custom CSS/styling
│   └── Mastech Digital-White 4.svg  # Company logo
│
└── scripts/
    └── check_naming.py           # Naming convention validator
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE (Medallion)                     │
├─────────────┬──────────────────┬────────────────────────────────┤
│   BRONZE    │      SILVER      │             GOLD                │
│  (Raw)      │  (Cleansed)      │  (Analytics-ready)             │
├─────────────┼──────────────────┼────────────────────────────────┤
│ SKU Master  │ SKU Cleansed     │ SKU Pricing Intelligence       │
│ Competitor  │ Competitor       │ Category Performance (Dynamic) │
│ Sales       │ Sales            │ Weekly Sell-Through             │
│ Promotions  │ Promotions       │ Promotion Performance          │
│ Loyalty     │ Loyalty          │ Loyalty Customer Insights       │
│ Returns     │ Returns          │ Returns Margin Analysis        │
│ Feed Log    │ DQ Check Log     │ Action Audit + Conversation    │
└─────────────┴──────────────────┴────────────────────────────────┘
        │                                       │
        │  TRANSFORM_BRONZE_TO_SILVER_PIPELINE  │  REFRESH_GOLD_LAYER_PIPELINE
        │  RUN_DATA_QUALITY_VALIDATION_SUITE    │  (includes Cortex AI recommendations)
        └───────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     CORTEX AI AGENT                               │
├─────────────────────────────────────────────────────────────────┤
│ Tool: query_pricing_data (cortex_analyst_text_to_sql)           │
│ Tool: execute_sku_action (REPRICE/REPLENISH/MONITOR/ESCALATE)   │
│ Tool: get_category_health (category KPI summary)                │
│ Tool: get_pricing_alerts (urgent repricing needs)               │
│ Semantic View: RETAIL_CATEGORY_PRICING_ANALYTICS                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task DAG (Daily Pipeline)

```
DAILY_TRANSFORM_PIPELINE_TRIGGER (6:00 AM UTC)
  └─> TRANSFORM_BRONZE_TO_SILVER
        └─> RUN_DATA_QUALITY_CHECKS
              └─> REFRESH_GOLD_ANALYTICS_LAYER
                    └─> GOLD_CATEGORY_PERFORMANCE_SUMMARY (auto-refresh via Dynamic Table)
```

Standalone (manual): `INGEST_COMPETITOR_PRICES_FROM_SERPAPI_TASK`

---

## Snowflake Objects Summary

| Layer | Objects | Count |
|-------|---------|-------|
| Bronze | Raw ingestion tables | 9 |
| Silver | Cleansed/enriched tables | 7 |
| Gold | Analytics tables | 7 |
| Snapshot | dbt SCD Type 2 | 1 |
| Dynamic Table | Auto-refresh category KPIs | 1 |
| Views | STG + INT + Analytics | 15 |
| Procedures (SQL) | Action, Health, Alerts | 3 |
| Procedures (Python) | Ingest, Transform, DQ, Gold | 4 |
| Tasks | DAG pipeline + manual | 5 |
| Stages | Internal (data + app) | 2 |
| Cortex Agent | Retail Category Analytics | 1 |
| Semantic View | Pricing Analytics | 1 |

---

---

## Key Conventions

| Item | Convention |
|------|-----------|
| Snowflake objects | `UPPER_SNAKE_CASE` |
| dbt model files | `lowercase_snake_case.sql` |
| dbt prefixes | `stg_` (staging), `int_` (intermediate), `fct_`/`dim_` (marts) |
| Agent folders | `lowercase-kebab-case` |
| Streams | `*_STREAM` suffix |
| Tasks | `*_TASK` suffix (advisory) |
| Bronze tables | `BRONZE_*_RAW` |
| Silver tables | `SILVER_*_CLEANSED` or `SILVER_*_ENRICHED` |
| Gold tables | `GOLD_*` |

---

## External Dependencies

| Service | Purpose | Integration |
|---------|---------|-------------|
| SerpAPI | Competitor price scraping | `SERPAPI_ACCESS_INTEGRATION` + `SERPAPI_NETWORK_RULE` |
| GitHub | Source control | `SF_GITHUB_INTEGRATION` |
| Snowflake Cortex | AI recommendations + Agent | Built-in (mistral-large2) |
