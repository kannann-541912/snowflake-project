# Category Intelligence Platform

**Category Intelligence · AI-Powered Pricing & Performance Portal**
Built on Snowflake · dbt · Cortex Agents · Semantic Views · Streamlit · SerpAPI

---

## Table of Contents

1. [Snowflake Features Used](#1-snowflake-features-used)
2. [Design Decision Records](#2-design-decision-records)
3. [Implementation Summary](#3-implementation-summary)
4. [Where Cortex Code (CoCo) Was Used](#4-where-cortex-code-coco-was-used)
5. [Snowflake Best Practices Applied](#5-snowflake-best-practices-applied)
6. [Roadmap: What's Next](#6-roadmap-whats-next)
7. [SQL Reference](#7-sql-reference)

---

## 1. Snowflake Features Used

| # | Snowflake Feature | Where It's Used | Why This Feature |
|---|---|---|---|
| 1 | **Medallion Architecture** | Full pipeline: Bronze → Silver → Gold | Clear lineage, layer isolation, independent refresh per layer |
| 2 | **Stored Procedures (Python)** | `INGEST_COMPETITOR_PRICES_FROM_SERPAPI`, `TRANSFORM_BRONZE_TO_SILVER_PIPELINE`, `RUN_DATA_QUALITY_VALIDATION_SUITE`, `REFRESH_GOLD_LAYER_PIPELINE`, `EXECUTE_SKU_ACTION` | Encapsulates ETL logic, callable from Tasks, Python for API integration |
| 3 | **Tasks (DAG)** | 5-task DAG: Trigger → Bronze→Silver → DQ Checks → Gold Refresh + Manual Ingest | Native scheduling, dependency chaining via AFTER clause, no external orchestrator |
| 4 | **dbt on Snowflake** | `Category_Intelligence` project - staging, intermediate, marts layers (views) | Declarative SQL, built-in testing, lineage graph, modular deployment |
| 5 | **Dynamic Tables** | `GOLD_CATEGORY_PERFORMANCE_SUMMARY` - auto-refreshes from Gold pricing intelligence | Incremental refresh without manual scheduling |
| 6 | **Cortex Agents** | Category intelligence agent with semantic view data access | Native LLM with data tools, no external API keys, NL to SQL |
| 7 | **Semantic Views (Cortex Analyst)** | `RETAIL_CATEGORY_PRICING_ANALYTICS` - 5 analytics views for pricing, promotions, loyalty, returns, category performance | NL to SQL translation, schema abstraction for agent queries |
| 8 | **Streamlit in Snowflake** | `CATEGORY_INTELLIGENCE_PLATFORM` - 4 tabs: Category, Promotions & Campaigns, Customer Loyalty, Returns & Margin Impact | Zero hosting, direct session access, no credential management |
| 9 | **External Access Integration** | `SERPAPI_ACCESS_INTEGRATION` for competitor price feeds from Google Shopping API | Secure outbound HTTP from Snowpark, API key in Secrets |
| 10 | **Secrets** | `SERPAPI_ACCESS_CREDENTIALS` - stores SerpAPI key | Native secret management, no plaintext credentials in code |
| 11 | **RBAC** | `RETAIL_CATEGORY_ANALYTICS_ROLE` with least-privilege grants | Separation of concerns, principle of least privilege |
| 12 | **Warehouse Auto-Suspend/Resume** | `RETAIL_CATEGORY_ANALYTICS_WH` (auto-suspend, auto-resume) | Cost efficiency, zero cold-start friction |
| 13 | **Internal Stages** | `RAW_DATA_UPLOAD_STAGE` (CSV ingestion), `CATEGORY_INTELLIGENCE_APP_STAGE` (Streamlit files) | Structured file management for data loads and app deployment |
| 14 | **Data Quality Validation** | `SILVER_DATA_QUALITY_CHECK_LOG` - row-level pass/fail with sample failures as VARIANT | Pre-Gold validation, root-cause traceability |
| 15 | **Snapshot (dbt)** | `SNAPSHOT_PRICING_INTELLIGENCE` - SCD Type 2 tracking of pricing changes | Historical price tracking for trend analysis |

---

## 2. Design Decision Records

Each row documents a key design decision, the options evaluated, why we chose what we chose, the impact of that decision, and the trade-off accepted.

### 2.1 Data Architecture

| Decision | Options Considered | Option Chosen | Why | Impact | Trade-off |
|---|---|---|---|---|---|
| Data Layer Pattern | Flat tables, Star schema, **Medallion (Bronze→Silver→Gold)** | Medallion | Clear separation of raw/validated/analytics-ready; enables independent refresh per layer | Full data lineage and reprocessability from source | Additional effort to build 3 layers instead of 1 |
| Bronze Load Strategy | API direct-to-Silver, Streams, **Raw JSON preservation** | Raw JSON preservation | Full SerpAPI response preserved for reprocessing; no data loss from parsing decisions | Complete reprocessability; schema evolution safe | Requires VARIANT parsing in Silver layer |
| Silver Enrichment | Simple type-cast only, **Join + compute derived fields** | Join + compute | Price gap calculations, competitive positioning flags, and stock status derived at Silver | Rich analytical fields available for Gold without re-joins | More complex Silver SPs |
| Gold Materialisation | Views only, Dynamic Tables, **Hybrid (dbt views + Dynamic Tables + tables)** | Hybrid | dbt for complex logic with testing; Dynamic Tables for auto-refresh summaries; tables for agent-populated data | Best tool for each use case | Multiple refresh mechanisms to understand |
| dbt Model Materialisation | Tables, Ephemeral, **Views** | Views | Zero storage cost for transformation logic; always reflects latest Silver data | Real-time data without refresh lag | Compute on every query (acceptable for small dataset) |

### 2.2 Data Quality

| Decision | Options Considered | Option Chosen | Why | Impact | Trade-off |
|---|---|---|---|---|---|
| DQ Framework | Great Expectations, dbt tests only, **Custom validation SP** | Custom SP | Full control over validation logic, row-level failure capture, VARIANT sample storage | Pre-Gold validation prevents bad data entering analytics | Custom code to maintain per validation rule |
| DQ Enforcement Point | Post-Gold (dbt test), **Pre-Gold (shift left)** | Pre-Gold | Bad data never enters Gold; downstream consumers always see clean data | Zero DQ debt accumulation in analytics layer | Additional SP complexity |
| Audit Granularity | Aggregate counts only, **Aggregate + sample failing rows** | Both | Aggregate for dashboards, sample rows (VARIANT) for root-cause investigation | Full traceability from failure to source record | Larger audit log table |
| DQ Trigger | Manual only, **Task-chained (after Silver transform)** | Task-chained | Automatic DQ on every pipeline run; no manual intervention needed | Consistent quality enforcement | DQ checks add pipeline latency |

### 2.3 AI / LLM Layer

| Decision | Options Considered | Option Chosen | Why | Impact | Trade-off |
|---|---|---|---|---|---|
| LLM Integration | OpenAI API, Cortex COMPLETE(), **Cortex Agents** | Cortex Agents | Native data tools (Cortex Analyst), no API keys, multi-step reasoning | Agent queries live pricing data without hand-coded SQL | Newer feature; less community documentation |
| Agent Data Access | Hard-coded SQL, Stage YAML, **Semantic Views** | Semantic Views | NL→SQL with dimension/fact declarations; schema changes don't break agent | Agent adapts to schema evolution automatically | Semantic view must be kept in sync with underlying views |
| Semantic View Scope | Single monolithic view, **Multi-view (5 analytics views)** | Multi-view | Each view optimised for its domain (pricing, promotions, loyalty, returns, category) | Better NL→SQL accuracy per domain | More views to maintain and keep in sync |
| AI Recommendations | Display-only, **Persist to Gold table** | Persist to Gold | AI pricing recommendations stored in `GOLD_SKU_PRICING_INTELLIGENCE` for action tracking | Full AI decision audit trail | Additional storage and refresh logic |

### 2.4 Application Layer

| Decision | Options Considered | Option Chosen | Why | Impact | Trade-off |
|---|---|---|---|---|---|
| UI Framework | React + FastAPI, Snowsight Dashboards, **Streamlit in Snowflake** | Streamlit in Snowflake | Zero hosting, direct Snowflake session, no credential management | No data egress, instant access to all objects | Limited UI customisation vs React |
| App Structure | Single page, **Multi-tab (4 tabs + sidebar + agent chat)** | Multi-tab | Logical separation: Category, Promotions, Loyalty, Returns; agent chat for ad-hoc queries | Users navigate to relevant domain quickly | More complex state management |
| Write Path | Direct SQL from UI, **Stored Procedures** | Stored Procedures | `EXECUTE_SKU_ACTION` encapsulates business logic, prevents SQL injection, auditable | Consistent write patterns, single point of change | Additional SP per write operation |
| Action Audit | No audit, **Immutable audit log** | Immutable audit log | `GOLD_ACTION_EXECUTION_AUDIT` captures every SKU action with before/after state | Full accountability for pricing decisions | Storage growth over time |
| Agent Interaction Log | No logging, **Conversation log table** | Conversation log | `GOLD_AGENT_CONVERSATION_LOG` captures question, response, SQL, latency | Agent performance monitoring and user behavior analysis | Additional write on every interaction |

### 2.5 Security & Governance

| Decision | Options Considered | Option Chosen | Why | Impact | Trade-off |
|---|---|---|---|---|---|
| Access Model | ACCOUNTADMIN for all, Schema-level grants, **Custom role** | Custom role (`RETAIL_CATEGORY_ANALYTICS_ROLE`) | Least privilege; app only sees what it needs | Reduced blast radius of compromised credentials | More grant management upfront |
| API Key Storage | Environment variable, Config file, **Snowflake Secrets** | Snowflake Secrets | Native, RBAC-governed, referenced by External Access Integration | Key never exposed in code or logs | Requires integration setup |
| External Network Access | Direct HTTP, VPN, **External Access Integration with network rules** | External Access Integration | Whitelisted outbound only (SerpAPI endpoint), auditable | Controlled egress, no broad internet access | Setup complexity per external service |

### 2.6 External Integrations

| Decision | Options Considered | Option Chosen | Why | Impact | Trade-off |
|---|---|---|---|---|---|
| Competitor Price Source | Web scraping, Manual CSV, **SerpAPI (Google Shopping)** | SerpAPI | Structured JSON responses, reliable API, broad retailer coverage | Real-time competitor pricing across major retailers | API credit cost per query |
| Ingestion Pattern | Scheduled auto-fetch, **Manual trigger (preserves API credits)** | Manual trigger | SerpAPI credits are finite; manual control prevents waste during development | Cost-controlled ingestion; explicit human decision to fetch | Requires manual execution or deliberate Task resume |
| Feed Observability | No logging, **Run log table** | Run log (`BRONZE_SERPAPI_FEED_RUN_LOG`) | Tracks execution status, SKU counts, error rates, API credit consumption | Full observability per feed run | Additional table to maintain |

---

## 3. Implementation Summary

### 3.1 Architecture

```
External Sources (SerpAPI, CSV Uploads, Openflow Runtime)
          │
          ▼
    ┌─────────────┐
    │   BRONZE    │  9 tables — raw data preservation
    │             │  (SKU master, competitor prices, sales,
    │             │   promotions, loyalty, returns, feed log)
    └─────────────┘
          │
          │  Python SPs (transform + enrich + validate)
          ▼
    ┌─────────────┐
    │   SILVER    │  6 tables — cleansed, enriched, validated
    │             │  + Data Quality Check Log
    └─────────────┘
          │
          │  Python SPs + Dynamic Tables + dbt views
          ▼
    ┌─────────────┐
    │    GOLD     │  8 tables — analytics-ready
    │             │  + 1 Dynamic Table (Category Performance)
    └─────────────┘
          │
          ├──► dbt Project (staging → intermediate → marts views)
          │
          ├──► Cortex Agent + Semantic View (5 analytics views)
          │
          └──► Streamlit App (4 tabs + Agent Chat + Action Audit)
```

### 3.2 Key Components

| Component | Objects | Purpose |
|---|---|---|
| Bronze Layer | 9 tables | Raw data preservation (SKU, prices, sales, promotions, loyalty, returns, feed log) |
| Silver Layer | 6 tables + DQ log | Validated, enriched data with price gaps and competitive positioning |
| Gold Layer | 8 tables + 1 Dynamic Table | Analytics-ready pricing intelligence, category performance, loyalty insights, promotion results, returns analysis |
| dbt Project | Staging (5 views) + Intermediate (5 views) + Marts (views) + 1 Snapshot | Declarative transformation layer with testing |
| AI Agent | 1 Cortex Agent + 1 Semantic View (5 underlying analytics views) | Natural language querying across all analytics domains |
| Application | Streamlit app (4 tabs) + Agent chat + Action SPs | Category Intelligence dashboard with pricing actions |
| External Integration | SerpAPI External Access + Secrets + Feed Log | Competitor price ingestion from Google Shopping |
| Scheduling | 5 Tasks (DAG-chained) | Daily pipeline: Trigger → Transform → DQ → Gold Refresh |
| Governance | Custom role + External Access Integration + Secrets | Least-privilege access + secure API connectivity |

### 3.3 Task DAG

```
DAILY_TRANSFORM_PIPELINE_TRIGGER (CRON 0 6 * * * UTC)
          │
          ▼
TRANSFORM_BRONZE_TO_SILVER
          │
          ▼
RUN_DATA_QUALITY_CHECKS
          │
          ▼
REFRESH_GOLD_ANALYTICS_LAYER

INGEST_COMPETITOR_PRICES_FROM_SERPAPI (Manual trigger - suspended)
```

### 3.4 Semantic View

| View | Underlying Analytics Views | Domain |
|---|---|---|
| `RETAIL_CATEGORY_PRICING_ANALYTICS` | `PRICING_INTELLIGENCE_ANALYTICS_VIEW` | SKU pricing & competitive gaps |
| | `PROMOTION_PERFORMANCE_ANALYTICS_VIEW` | Campaign ROAS & uplift |
| | `LOYALTY_CUSTOMER_ANALYTICS_VIEW` | Customer LTV & churn risk |
| | `RETURNS_MARGIN_ANALYTICS_VIEW` | Return rates & margin erosion |
| | `CATEGORY_PERFORMANCE_ANALYTICS_VIEW` | Category-level KPIs |

### 3.5 dbt Project Structure

```
Category_Intelligence/
├── dbt_project.yml
├── profiles.yml
├── models/
│   ├── staging/          (5 views: stg_pricing, stg_returns, stg_loyalty, stg_promotions, stg_category)
│   ├── intermediate/     (5 views: int_pricing, int_returns, int_loyalty, int_promotions, int_category)
│   └── marts/            (analytics-ready views)
└── snapshots/
    └── snapshot_pricing_intelligence (SCD Type 2)
```

---

## 4. Where Cortex Code (CoCo) Was Used

CoCo was used as the AI development assistant across the entire project lifecycle.

### 4.1 By Component

| Component | What CoCo Did |
|---|---|
| **Bronze Layer** | Generated all table DDL with VARIANT columns for SerpAPI JSON; built CSV load scripts via internal stage |
| **Silver SPs** | Created Python stored procedures for Bronze→Silver transformation with enrichment logic (price gaps, competitive positioning, margin calculations) |
| **Data Quality** | Authored validation suite SP with row-level failure capture and VARIANT sample storage |
| **Gold Layer** | Built Gold refresh pipeline SP with Cortex AI recommendations; created Dynamic Table for category performance |
| **dbt Project** | Wrote all staging/intermediate/marts models; generated dbt_project.yml, profiles.yml, schema.yml; configured snapshot for pricing SCD |
| **Cortex Agent** | Configured agent with semantic view data access; created 5 analytics views for multi-domain NL to SQL |
| **Semantic View** | Created `RETAIL_CATEGORY_PRICING_ANALYTICS` with proper dimension/fact declarations across 5 underlying views |
| **Streamlit App** | Designed 4-tab layout with agent chat, KPI cards, action buttons, custom dark theme, and write-back SPs |
| **External Integration** | Set up SerpAPI External Access Integration, network rules, secrets, and Python ingestion SP |
| **Task DAG** | Created 5-task DAG with AFTER dependency chaining and CRON schedule |
| **RBAC** | Authored role grants, warehouse configuration, schema permissions |
| **Troubleshooting** | Diagnosed agent errors, warehouse session binding, semantic view configuration, External Access permission issues |

### 4.2 CoCo Capabilities Used

| Capability | Example |
|---|---|
| SQL Execution | Ran queries to validate views, check grants, verify data, resume warehouses |
| Schema Exploration | `SHOW OBJECTS`, `SHOW GRANTS`, `SHOW TASKS`, `SHOW STAGES` to map the full schema |
| Snowflake Docs Lookup | Found correct syntax for Cortex Agents, semantic views, External Access Integrations, dbt deployment |
| Error Diagnosis | Traced agent data access errors, External Access permission issues, dbt compilation failures |
| Code Generation | SQL DDL, Python SPs, dbt models, Streamlit UI, agent configuration |
| File Operations | Created workspace files for Streamlit app, dbt project, architecture documentation |
| Grant Analysis | Identified missing grants, verified role permissions for External Access and Secrets |

### 4.3 CoCo by Lifecycle Phase

```
DESIGN     → Architecture decisions, medallion layer design, integration patterns
BUILD      → SQL DDL, Python SPs, dbt models, Streamlit UI, agent config, semantic views
TEST       → Query validation, DQ suite verification, dbt test execution, view health checks
DEPLOY     → Task scheduling, Streamlit deployment, dbt project configuration
OPERATE    → Error diagnosis, warehouse resume, pipeline monitoring, feed log analysis
DOCUMENT   → Architecture documentation, schema analysis, best practices
```

---

## 5. Snowflake Best Practices Applied

### 5.1 Data Architecture

| Best Practice | Implementation | Impact |
|---|---|---|
| Medallion Architecture | 3 layers with consistent `BRONZE_`/`SILVER_`/`GOLD_` prefixes | Full lineage from source to analytics |
| Immutable Bronze | No UPDATE/DELETE on Bronze — raw preservation only | Guaranteed reprocessability |
| JSON Preservation | Full SerpAPI response stored as VARIANT in Bronze | Schema evolution safe; no data loss |
| Enrichment at Silver | Price gaps, competitive flags, margin calculations computed at Silver | Gold layer is clean consumption-ready |
| Hybrid Gold | Tables (SP-populated) + Dynamic Tables (auto-refresh) + dbt views | Best tool for each refresh pattern |

### 5.2 Data Quality

| Best Practice | Implementation | Impact |
|---|---|---|
| Pre-Gold Validation | DQ checks run after Silver transform, before Gold refresh | Bad data never enters analytics layer |
| Row-Level Audit | Individual failures logged to `SILVER_DATA_QUALITY_CHECK_LOG` with sample rows | Root-cause traceable to source record |
| Task-Chained DQ | DQ is a mandatory step in DAG (between Silver and Gold) | Cannot skip validation |
| Informational DQ | DQ does not block Gold (logs warnings) | Pipeline resilience; manual review for failures |

### 5.3 Compute & Cost

| Best Practice | Implementation | Impact |
|---|---|---|
| Right-Sized Warehouse | `RETAIL_CATEGORY_ANALYTICS_WH` for sub-1000 row workload | Minimum credit consumption |
| Auto-Suspend/Resume | Idle warehouse suspends automatically | Near-zero idle cost |
| API Credit Governance | SerpAPI ingestion task suspended by default (manual trigger) | No accidental API credit spend |
| Feed Run Logging | `BRONZE_SERPAPI_FEED_RUN_LOG` tracks credit consumption per run | Cost observability per ingestion |
| dbt Views (not tables) | All dbt models materialised as views | Zero storage cost for transformation layer |

### 5.4 Security & Governance

| Best Practice | Implementation | Impact |
|---|---|---|
| Custom App Role | `RETAIL_CATEGORY_ANALYTICS_ROLE` — least privilege | Reduced blast radius |
| Snowflake Secrets | API keys stored in native Secrets object | No plaintext credentials anywhere |
| External Access Integration | Whitelisted outbound to SerpAPI only | Controlled network egress |
| Action Audit Trail | `GOLD_ACTION_EXECUTION_AUDIT` logs every pricing action | Full accountability |
| Agent Conversation Log | `GOLD_AGENT_CONVERSATION_LOG` captures all interactions | AI usage auditable |

### 5.5 AI Agent Operations

| Best Practice | Implementation | Impact |
|---|---|---|
| Semantic Layer for Agents | Agent accesses data via semantic view only | Schema changes don't break agent |
| Multi-View Architecture | 5 domain-specific analytics views behind one semantic view | Better NL→SQL accuracy per domain |
| Conversation Persistence | Every agent interaction logged with SQL, response, latency | Performance monitoring and audit |
| Domain Routing | Semantic view comment guides agent to correct underlying view | Reduced hallucination on cross-domain queries |

### 5.6 Operations

| Best Practice | Implementation | Impact |
|---|---|---|
| Task DAG | AFTER clause chains Transform → DQ → Gold | Prevents stale-data in analytics |
| Daily CRON Schedule | 6 AM UTC trigger for full pipeline refresh | Fresh data for business day |
| Manual Ingest Control | SerpAPI task suspended — explicit trigger only | API cost governance |
| Consistent Naming | Layer prefix (`BRONZE_`, `SILVER_`, `GOLD_`) on all tables | Instant object classification |
| Feed Observability | Run log with status, counts, errors, duration | Operational visibility per ingestion |

---

## 6. Roadmap: What's Next

Features and capabilities not yet implemented but planned for future iterations:

### 6.1 Advanced AI Capabilities (Not Yet Implemented)

| Feature | What It Would Add | Status |
|---|---|---|
| **Agent Evaluation** | Score agent outputs against ground-truth pricing decisions | Planned — use Cortex AI Evaluation framework |
| **Agent Observability** | Log token usage, latency, tool call success rate per request | Planned — Cortex AI Observability procedures available |
| **Verified Queries (VQR)** | Add validated query examples to semantic view for improved NL→SQL accuracy | Planned — reduces hallucination on complex filters |
| **Multi-Agent Architecture** | Separate agents for pricing, promotions, loyalty, and returns domains | Evaluating — currently single agent handles all domains |

### 6.2 Data Platform Enhancements (Not Yet Implemented)

| Feature | What It Would Add | Status |
|---|---|---|
| **Streams + Tasks (CDC)** | Incremental Bronze → Silver instead of full transform | Evaluating — beneficial as data volume grows |
| **More Dynamic Tables** | Replace batch Gold refresh with auto-refreshing Gold layer | Evaluating — suitable for high-frequency pricing updates |
| **Cortex Search** | Full-text search over product descriptions and competitor listings | Planned — for product matching improvement |
| **Data Classification** | Snowflake auto-classification for sensitive pricing data | Planned — tag competitive intelligence columns |

### 6.3 ML Capabilities (Not Yet Implemented)

| Feature | What It Would Add | Status |
|---|---|---|
| **Price Elasticity Model** | ML model predicting optimal price points per SKU | Planned — scikit-learn + Snowflake ML Registry |
| **Demand Forecasting** | Time-series prediction for inventory planning | Planned — leverage weekly sales history |
| **Churn Prediction** | Predict loyalty member churn risk from transaction patterns | Evaluating — data available in loyalty tables |
| **Automated Repricing** | ML-driven price recommendations executed automatically | Future — requires human-in-the-loop validation first |

### 6.4 Governance & Security (Not Yet Implemented)

| Feature | What It Would Add | Status |
|---|---|---|
| **Column-Level Masking** | Protect competitive pricing data from unauthorized roles | Planned — mask competitor margins and cost data |
| **Row-Level Security** | Restrict SKU visibility by category manager assignment | Planned — requires row access policies on Gold tables |
| **Tag-Based Masking** | Auto-mask columns tagged as competitive intelligence | Planned — after data classification is applied |

---

## 7. SQL Reference

Key operational queries consolidated here for reference.

### 7.1 Setup

```sql
CREATE DATABASE IF NOT EXISTS DEMO_DEV;
CREATE SCHEMA  IF NOT EXISTS DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT;
CREATE ROLE    IF NOT EXISTS RETAIL_CATEGORY_ANALYTICS_ROLE;
CREATE WAREHOUSE IF NOT EXISTS RETAIL_CATEGORY_ANALYTICS_WH
    WAREHOUSE_SIZE = 'X-SMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;

GRANT USAGE ON WAREHOUSE RETAIL_CATEGORY_ANALYTICS_WH TO ROLE RETAIL_CATEGORY_ANALYTICS_ROLE;
GRANT USAGE ON DATABASE  DEMO_DEV TO ROLE RETAIL_CATEGORY_ANALYTICS_ROLE;
GRANT USAGE ON SCHEMA    DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT TO ROLE RETAIL_CATEGORY_ANALYTICS_ROLE;
```

### 7.2 Pipeline Execution

```sql
-- Full daily pipeline (triggered automatically at 6 AM UTC)
EXECUTE TASK DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.DAILY_TRANSFORM_PIPELINE_TRIGGER;

-- Manual Bronze→Silver transform
CALL DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.TRANSFORM_BRONZE_TO_SILVER_PIPELINE();

-- Manual DQ validation
CALL DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.RUN_DATA_QUALITY_VALIDATION_SUITE('MANUAL');

-- Refresh Gold layer
CALL DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.REFRESH_GOLD_LAYER_PIPELINE(NULL);

-- Ingest competitor prices (manual — preserves API credits)
CALL DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.INGEST_COMPETITOR_PRICES_FROM_SERPAPI('MANUAL', 100);
```

### 7.3 Task Scheduling

```sql
-- Daily pipeline trigger (root task)
CREATE OR REPLACE TASK DAILY_TRANSFORM_PIPELINE_TRIGGER
    WAREHOUSE = RETAIL_CATEGORY_ANALYTICS_WH
    SCHEDULE  = 'USING CRON 0 6 * * * UTC'
AS SELECT 'DAILY_TRANSFORM_PIPELINE_STARTED' AS status;

-- Bronze→Silver (after trigger)
CREATE OR REPLACE TASK TRANSFORM_BRONZE_TO_SILVER
    WAREHOUSE = RETAIL_CATEGORY_ANALYTICS_WH
    AFTER DAILY_TRANSFORM_PIPELINE_TRIGGER
AS CALL TRANSFORM_BRONZE_TO_SILVER_PIPELINE();

-- DQ checks (after Silver)
CREATE OR REPLACE TASK RUN_DATA_QUALITY_CHECKS
    WAREHOUSE = RETAIL_CATEGORY_ANALYTICS_WH
    AFTER TRANSFORM_BRONZE_TO_SILVER
AS CALL RUN_DATA_QUALITY_VALIDATION_SUITE('TASK_SCHEDULED');

-- Gold refresh (after DQ)
CREATE OR REPLACE TASK REFRESH_GOLD_ANALYTICS_LAYER
    WAREHOUSE = RETAIL_CATEGORY_ANALYTICS_WH
    AFTER RUN_DATA_QUALITY_CHECKS
AS CALL REFRESH_GOLD_LAYER_PIPELINE(NULL);
```

### 7.4 Monitoring

```sql
-- Latest SerpAPI feed runs
SELECT run_id, triggered_by, status, skus_fetched, errors, api_credits_used, duration_seconds
FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.BRONZE_SERPAPI_FEED_RUN_LOG
ORDER BY created_at DESC LIMIT 10;

-- Data quality check summary
SELECT check_name, table_name, status, rows_checked, rows_failed, failure_rate
FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.SILVER_DATA_QUALITY_CHECK_LOG
ORDER BY executed_at DESC LIMIT 20;

-- Agent conversation history
SELECT question, response_summary, sql_generated, latency_ms
FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_AGENT_CONVERSATION_LOG
ORDER BY created_at DESC LIMIT 10;

-- Action audit trail
SELECT sku_id, action_type, before_state, after_state, executed_by, executed_at
FROM DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GOLD_ACTION_EXECUTION_AUDIT
ORDER BY executed_at DESC LIMIT 10;
```

### 7.5 Query Semantic View

```sql
-- Query pricing intelligence via semantic view
SELECT * FROM TABLE(
    DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.RETAIL_CATEGORY_PRICING_ANALYTICS!QUERY(
        'What are the top 10 SKUs with the largest competitor price gap?'
    )
);

-- Category health check
CALL DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GET_CATEGORY_HEALTH(NULL);

-- Pricing alerts
CALL DEMO_DEV.RETAIL_CATEGORY_ANALYTICS_AGENT.GET_PRICING_ALERTS(NULL, 10);
```
