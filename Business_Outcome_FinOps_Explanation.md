
# FinOps Value Intelligence
## Technical Brief 
---

## 30-Second Summary

Enterprises running Snowflake know what they spend. They do not know what that spend
returns. This application joins compute cost to business outcome — fraud detected,
SARs filed, losses prevented — at a daily queryable grain, then puts a governed
conversational AI layer on top of it. The result is a system where a CTO can ask
*"what did yesterday's compute investment protect?"* and get a specific, auditable
answer in seconds. Built entirely inside Snowflake. Zero external dependencies.
Production-ready in five SQL files and one Python file.

---

## Key Value Proposition - Fraud Intelligence Solution is taken as an example. Applicable for cross functional solutions as well

| For | The Value |
|---|---|
| **CTO** | Every credit spent on `AGENT_DEMO_WH` is now accountable to a business outcome. Invest more where ROI is high. Cut where it is not. |
| **CFO** | $0.09 compute cost per SAR filed. The cost of inaction — a missed SAR — is orders of magnitude higher. FinOps becomes a risk conversation, not a cost conversation. |
| **CCO / Compliance** | Audit trail from compute query to fraud decision to SAR filing date. Regulatory defensibility built into the data layer. |
| **Platform Engineering** | Reference architecture for joining `ACCOUNT_USAGE` to any business domain. Fraud today. Revenue, clinical, trading tomorrow. |

---

> **"We are not optimising cost. We are optimising decisions on where to invest compute."**

---

## Table of Contents

- [Purpose](#purpose)
- [Architecture Overview](#architecture-overview)
- [Layer-by-Layer Breakdown](#layer-by-layer-breakdown)
- [Three Technical Decisions That Matter](#three-technical-decisions-that-matter)
- [How the Cortex Analyst Layer Works](#how-the-cortex-analyst-layer-works)
- [The Architectural Argument](#the-architectural-argument)
- [Repository Structure](#repository-structure)

---

## Purpose

Most organisations running Snowflake have solved the wrong problem. They have dashboards
that tell them what they spent. They have resource monitors that cap what they can spend.
What they do not have is a system that tells them whether the spend was worth it — and more
importantly, where to spend next.

This application makes that argument in production code, not in a slide deck.

---

## Architecture Overview

```
SNOWFLAKE.ACCOUNT_USAGE          ← Raw compute telemetry (365 days)
        ↓
DEMO_DEV.FINOPS_CURATED          ← Optimised attribution tables
        ↓
DEMO_DEV.FRAUD_INTELLIGENCE      ← Business outcome layer (GLD tier)
        ↓
ADMIN_DB.OPS (COST_VALUE_MAPPING)← Cost-to-value grain: 1 row per day
        ↓
ADMIN_DB.OPS (Semantic View)     ← Governed analytical contract
        ↓
Cortex Agent + Analyst tool      ← Conversational intelligence layer
        ↓
Streamlit in Snowflake           ← Warehouse runtime UI
```

This is not a FinOps dashboard. It is a **cost-to-value attribution engine** with a
conversational intelligence layer sitting on top of it.

---

## Layer-by-Layer Breakdown

### Layer 1 — ACCOUNT_USAGE

Snowflake's native telemetry — `WAREHOUSE_METERING_HISTORY`, `QUERY_HISTORY`,
`METERING_HISTORY` — provides 365 days of granular compute telemetry at no additional
cost. Most organisations query this reactively, once a month, when the bill arrives.
This architecture queries it continuously and with intent.

### Layer 2 — FINOPS_CURATED

Raw telemetry is not analysis-ready. `WAREHOUSE_METERING_HISTORY` gives hourly credit
buckets. `QUERY_HISTORY` gives query execution times. Neither gives cost per query.

A **proportional credit attribution model** allocates hourly warehouse credits to
individual queries by elapsed time share. This calculation makes unit economics possible.
Without it, every downstream insight is directional at best.

Three curated tables are produced:

| Table | Source | Purpose |
|---|---|---|
| `WH_DAILY_USAGE` | `WAREHOUSE_METERING_HISTORY` | Idle vs productive credits per warehouse per day |
| `QUERY_COST_PATTERN` | `QUERY_HISTORY` | Per-query cost attribution by user, schema, type |
| `SPCS_DAILY_USAGE` | `METERING_HISTORY` | AI infrastructure credit tracking |

### Layer 3 — Business Data Join

This is where this application separates from every generic FinOps tool in the market.

Compute cost is joined to `DEMO_DEV.FRAUD_INTELLIGENCE.GLD_ALERT_ENRICHED` — carrying
`IS_FRAUD_DERIVED`, `ML_FRAUD_SCORE`, `DISPOSITION`, and `SAR_FILED` as first-class
columns. The result is `COST_VALUE_MAPPING` — one row per day, carrying both the compute
cost of running `AGENT_DEMO_WH` and the fraud outcomes that compute produced.

**Value is measured in three dimensions, not one:**

| Dimension | Metric | Why It Matters |
|---|---|---|
| Financial | `FRAUD_AMOUNT_PROTECTED` per credit | Direct ROI of compute investment |
| Regulatory | `SAR_COST_PER_FILING` | Compliance cost vs exposure risk |
| Operational | Detection rate × alert volume | Compute replacing L1 analyst labour |

At **$0.09 compute cost per SAR filing**, the regulatory dimension alone reframes the
entire cost conversation. A missed SAR is not a $0.09 problem. It is a six-figure
compliance exposure. The compute cost becomes noise against that backdrop.

### Layer 4 — Semantic View

```sql
CREATE OR REPLACE SEMANTIC VIEW
    ADMIN_DB.OPS.FINOPS_VALUE_INTELLIGENCE_SV
```

Snowflake's `CREATE SEMANTIC VIEW` is a GA object that defines measures, dimensions, and
verified queries in a governed, reusable layer. Nine measures are defined as first-class
analytical objects with business descriptions — including `FRAUD_AMOUNT_PER_CREDIT` and
`SAR_COST_PER_FILING`.

Four verified queries anchor the semantic model around the decisions a CTO or CFO
actually needs to make:

| Query | Business Question |
|---|---|
| `fraud_value_per_credit_this_month` | Where is value being created? |
| `sar_filing_cost_this_month` | What does regulatory compliance cost in compute? |
| `pending_alerts_by_rule` | Where should analyst time be invested? |
| `worst_cost_efficiency_days` | What happened on our worst days? |

The semantic view is not a view in the traditional SQL sense. It is a
**machine-readable contract** between your data and your AI layer.

### Layer 5 — Cortex Agent + Analyst Tool

Cortex Analyst consumes the semantic view and translates natural language directly into
governed SQL — not approximate SQL, not hallucinated column names, but SQL structurally
constrained by defined measures and dimensions.

> As of April 2026, Cortex Agents with Analyst as tool generate SQL directly rather than
> delegating to a separate service step — lower latency, higher accuracy on every query.

The agent does not have access to raw tables. It has access to a semantic contract.
That distinction matters enormously for governance.

---

## Three Technical Decisions That Matter

### 1. Warehouse Runtime Over Container Runtime

Streamlit in Snowflake supports two runtimes. Container runtime offers flexibility.
Warehouse runtime delivers governance, zero credential management, implicit session
context, and no external network surface.

For an application sitting on top of fraud data and regulatory filing metrics, container
runtime is the wrong choice regardless of its technical capabilities.

```python
# Session obtained implicitly — no credentials, no connection strings
from snowflake.snowpark.context import get_active_session
session = get_active_session()
```

The security posture is inherited entirely from Snowflake RBAC.

### 2. Transparent Cost Simulation

`AGENT_DEMO_WH` had 6 days of real metering history overlapping with 79 days of fraud
alert history. Rather than constraining analysis to 6 data points, a proportional
simulation model was built — deriving a credits-per-alert rate from 6 real days and
back-filling 73 days proportionally.

Every simulated row carries `COST_IS_SIMULATED = TRUE`. The semantic view exposes this
as a queryable dimension. The agent answers "how much of this data is simulated?"
correctly.

> Intellectual honesty in a technical demo builds more credibility than a clean dataset
> that cannot withstand scrutiny.

### 3. Value Defined in Three Dimensions

Generic FinOps tools measure one dimension: financial value. This architecture measures
three simultaneously — financial, regulatory, and operational — making the cost
conversation relevant to the CFO, CCO, and COO simultaneously, not just engineering.

---

## How the Cortex Analyst Layer Works

When a user asks *"on my worst cost-efficiency days, what happened?"* — the agent
executes this chain in real time:

```
Natural language input
        ↓
Intent mapped to verified query in semantic view
        ↓
SQL generated, constrained by defined measures
        ↓
Executed against COST_VALUE_MAPPING
        ↓
Structured result + natural language interpretation returned
```

The SQL is available for inspection but not surfaced by default. This is a deliberate
UX decision — the audience is making investment decisions, not debugging SQL. The
verified query design ensures correctness before the demo starts. The agent is not
improvising.

---

## The Architectural Argument

Every enterprise running Snowflake has `ACCOUNT_USAGE`. Every enterprise has business
outcome data — revenue per pipeline run, patient throughput per clinical query, trades
processed per market data workload.

The gap in every case is the same: **no one has joined compute cost to business outcome
at a queryable grain, and no one has put a governed conversational layer on top of
that join.**

What was built in five SQL files, one Python file, and one semantic view is the
**reference architecture for that pattern**. The fraud domain is the proof of concept.
The pattern is the product.

The question for a CTO is not whether this is technically impressive. The question is:

> *What is the equivalent of `FRAUD_AMOUNT_PROTECTED` in your highest-cost Snowflake
> workload — and do you know what each credit spent on that workload is returning?*

If the answer is no, this architecture is the starting point.

---

## Repository Structure

```
finops-value-intelligence/
│
├── sql/
│   ├── 01_discover.sql               # Schema exploration — run first
│   ├── 02_finops_curated_setup.sql   # WH_DAILY_USAGE, QUERY_COST_PATTERN, SPCS
│   ├── 03_cost_value_mapping.sql     # Business join — cost × fraud outcome
│   ├── 04_simulate_cost.sql          # Transparent cost back-fill
│   └── 05_semantic_view.sql          # CREATE SEMANTIC VIEW DDL
│
├── app/
│   ├── 06_streamlit_app.py           # Streamlit in Snowflake — warehouse runtime
│   └── styles.py                     # Mastech brand theme + Plotly tokens
│
├── .streamlit/
│   └── config.toml                   # Dark theme + primary colour tokens
│
├── deploy/
│   └── deploy_app.sql                # Stage, upload, CREATE STREAMLIT sequence
│
└── FINOPS_VALUE_INTELLIGENCE.md      # This file
```

---

## Key Numbers

| Metric | Value |
|---|---|
| Alert records | 1,400 |
| Date range | Feb 2026 — May 2026 |
| Confirmed fraud alerts | 655 |
| SARs filed | 606 (May MTD) |
| Compute cost per SAR | $0.09 |
| Real metering days | 6 |
| Simulated metering days | 73 |
| Semantic view measures | 9 |
| Verified queries | 4 |
| Streamlit runtime | Warehouse |

---

*Built on Snowflake. Powered by Cortex. Governed by Design.*
