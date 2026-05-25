# agent — Cortex Agent Developer Guide

The `agent/` directory owns everything required to define, deploy, evaluate, and monitor the `TPCH_ANALYST` Cortex Agent: the natural-language data analyst for `SANDBOX.TPCH`.

## Directory Layout

```
agent/
├── prompts/
│   ├── orchestration.md       # System prompt — agent identity, tool rules, safety
│   └── response.md            # Response formatting instructions
├── specs/
│   ├── v1/
│   │   ├── agent_spec.json    # Versioned spec snapshot (tools, model, tool_resources)
│   │   └── metadata.yml       # Version changelog and status (draft → stable → deprecated)
│   └── README.md              # Spec versioning policy
├── evals/
│   ├── eval_config.yaml       # Eval suite config (judge model, thresholds, connection)
│   ├── ground_truth.json      # Question/answer pairs for LLM-as-judge scoring
│   ├── run_evals.py           # Eval runner — calls SNOWFLAKE.CORTEX.AI_JUDGE
│   └── results/               # Eval output written here (and to Snowflake table)
└── monitoring/
    ├── usage_queries.sql      # Operational queries — usage, latency, errors
    └── alert_policy.yml       # Alert thresholds and escalation policy
```

## Prerequisites

```bash
pip install snowflake-cli pyyaml
```

Configure your local Snowflake connection (see `config.toml.example` in the project root):

```bash
cp config.toml.example config.toml
# Edit config.toml — add your PAT token under [connections.default]
```

## Quickstart — Deploy the Agent

```bash
# Dry-run: inspect the SQL that will be sent to Snowflake
python scripts/deploy_agent.py --dry-run

# Deploy the current spec (v1) to SANDBOX.TPCH.TPCH_ANALYST
python scripts/deploy_agent.py | snow sql -c default --stdin

# Deploy a specific versioned spec
python scripts/deploy_agent.py --spec-version v1 | snow sql -c default --stdin
```

`deploy_agent.py` builds a `CREATE OR REPLACE AGENT` statement by merging `specs/v1/agent_spec.json` with the content of `prompts/orchestration.md` and `prompts/response.md`, then writes the SQL to stdout.

## Editing Prompts

All prompt changes live in `agent/prompts/`.

| File | What to change |
|------|---------------|
| `orchestration.md` | Agent scope, tool call rules, safety guardrails, in/out-of-scope examples |
| `response.md` | Output format, number formatting, length limits, tone |

After editing, redeploy with `deploy_agent.py` and run the eval suite to confirm no regressions.

## Versioning the Agent Spec

1. Copy `specs/v1/` to `specs/v2/`.
2. Edit `specs/v2/agent_spec.json` with your changes (new tools, different model, updated tool_resources).
3. Set `status: draft` in `specs/v2/metadata.yml` and document changes in its `changelog` field.
4. Run evals against the new version (see below).
5. If evals pass, set `status: stable` and open a PR.
6. After merge, CI deploys via `deploy_agent.py --spec-version v2`.

Never edit a released spec in-place — always create a new version directory.

## Running Evaluations

Evals use `SNOWFLAKE.CORTEX.AI_JUDGE` to score agent responses against ground-truth question/answer pairs.

```bash
pip install snowflake-connector-python pyyaml

# Run the full suite against the currently deployed agent
python agent/evals/run_evals.py

# Run against a specific spec version (pre-deploy testing)
python agent/evals/run_evals.py --spec-version v2

# Dry-run: validate config and ground truth file without calling Snowflake
python agent/evals/run_evals.py --dry-run
```

### Pass/fail thresholds (defined in `eval_config.yaml`)

| Criterion | Threshold |
|-----------|-----------|
| Overall weighted score | ≥ 0.80 |
| Any single question | ≥ 0.60 |
| Tool call accuracy | 1.00 (all questions must call the expected tool) |

Results are written to `agent/evals/results/` locally and to `SANDBOX.TPCH.AGENT_EVAL_RESULTS` in Snowflake.

## Adding Ground Truth Questions

Edit `agent/evals/ground_truth.json`. Each entry requires:

```json
{
  "question": "Who are the top 5 customers by revenue this quarter?",
  "expected_tool": "query_customer_orders",
  "reference_answer": "The top 5 customers by revenue are ..."
}
```

Keep questions representative of real user queries. Aim for at least 10 entries covering happy-path, edge case, and out-of-scope rejections.

## Monitoring

Operational SQL queries are in `agent/monitoring/usage_queries.sql`. Run them manually in Snowsight or wire them into a Snowflake Task for automated alerting.

Alert thresholds and escalation contacts are in `agent/monitoring/alert_policy.yml`. Update this file when ownership or SLOs change.

## CI/CD

| Workflow | Trigger | What runs |
|----------|---------|-----------|
| `validate.yml` | PR to `main` | `validate_agent_spec.py`, `deploy_agent.py --dry-run`, `run_evals.py --dry-run` |
| `deploy.yml` | Push to `main` | `deploy_agent.py` piped to `snow sql`, then full `run_evals.py` suite |
