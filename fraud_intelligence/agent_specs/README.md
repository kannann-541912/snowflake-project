# Agent Specs — Canonical Source of Truth

This folder contains the definitive agent specification YAML files for the Fraud Intelligence Platform.

**DO NOT create separate folders per agent.** All specs live here.

## Agents

| File | Agent | Schema | Purpose |
|------|-------|--------|---------|
| `triage_agent_spec.yaml` | `FRAUD_TRIAGE_AGENT` | `DEMO_DEV.FRAUD_INTELLIGENCE` | Produces examiner-ready investigation dossiers with ML scoring |
| `sar_agent_spec.yaml` | `FRAUD_SAR_AGENT` | `DEMO_DEV.FRAUD_INTELLIGENCE` | Drafts FinCEN-compliant SAR narratives for human review |

## Deploying Agents

Use `AGENT_DEMO_ROLE` and `AGENT_DEMO_WH`:

```sql
USE ROLE AGENT_DEMO_ROLE;
USE WAREHOUSE AGENT_DEMO_WH;

CREATE OR REPLACE AGENT DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_TRIAGE_AGENT
COMMENT = 'UC2 — Produces examiner-ready investigation dossiers for fraud alerts with ML scoring'
FROM SPECIFICATION $$ <paste triage_agent_spec.yaml contents> $$;

CREATE OR REPLACE AGENT DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_SAR_AGENT
COMMENT = 'UC3 — Drafts FinCEN-compliant SAR narratives for human analyst review'
FROM SPECIFICATION $$ <paste sar_agent_spec.yaml contents> $$;
```

## Tool Types Reference

| tool_spec.type | tool_resources key | Use for |
|----------------|-------------------|---------|
| `"generic"` | `type: "procedure"`, `identifier: "..."` | Stored procedures / UDFs |
| `"cortex_analyst_text_to_sql"` | `semantic_view: "..."` | Semantic views (Cortex Analyst) |
| `"cortex_search"` | `name: "..."` | Cortex Search services |

## Testing

```sql
SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(
    'DEMO_DEV.FRAUD_INTELLIGENCE.FRAUD_TRIAGE_AGENT',
    '{"messages": [{"role": "user", "content": [{"type": "text", "text": "Investigate alert ALT000424 for customer CUST00016"}]}]}'
);
```
