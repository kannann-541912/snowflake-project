# agent — AgentOps Developer Guide

The `agent/` directory owns the complete operational lifecycle of all Cortex Agents in this account. Each agent is self-contained in its own subfolder. A shared eval runner and deploy script work across all agents automatically.

## Directory Layout

```
agent/
├── deploy_all.py              # Deploy one or all agents via scripts/deploy_agent.py
├── run_evals.py               # Shared evaluation runner — works for any agent
└── agents/
    └── tpch-analyst/          # TPCH_ANALYST — data analyst for SANDBOX.TPCH
        ├── agent.yml          # Identity: name, fqn, database, schema, owner
        ├── specs/
        │   ├── README.md      # Spec versioning policy
        │   └── v1/
        │       ├── agent_spec.json   # Immutable versioned spec snapshot
        │       └── metadata.yml      # Version, status, changelog
        ├── prompts/
        │   ├── orchestration.md      # System prompt: scope, tool rules, safety
        │   └── response.md           # Output formatting rules
        ├── evals/
        │   ├── eval_config.yaml      # Judge model, thresholds, connection, result table
        │   ├── ground_truth.json     # Q&A pairs for LLM-as-judge scoring
        │   └── results/              # Eval run outputs (gitignored)
        └── monitoring/
            ├── usage_queries.sql     # Invocation, latency, credit, error queries
            └── alert_policy.yml      # Alert thresholds and Snowflake Alert DDL
```

## Prerequisites

```bash
pip install snowflake-cli pyyaml snowflake-connector-python
cp config.toml.example config.toml
# Edit config.toml — add your PAT under [connections.default]
```

## Discovering Agents

```bash
# List all agents discovered in agent/agents/
python agent/deploy_all.py --list
python agent/run_evals.py --list
```

## Deploying Agents

```bash
# Deploy all agents
python agent/deploy_all.py -c default

# Deploy a single agent
python agent/deploy_all.py -c default --agent tpch-analyst

# Dry-run: inspect the SQL without executing
python agent/deploy_all.py --dry-run -c default
```

Internally, `deploy_all.py` calls `scripts/deploy_agent.py --agent <name>` per agent, which merges the spec JSON with `prompts/orchestration.md` and `prompts/response.md` into a `CREATE OR REPLACE AGENT` statement.

## Running Evaluations

```bash
# Run evals for a specific agent
python agent/run_evals.py --agent tpch-analyst

# Run evals for ALL agents
python agent/run_evals.py --all

# Run a single question by ID
python agent/run_evals.py --agent tpch-analyst --question-id GT-001

# Run a question category
python agent/run_evals.py --agent tpch-analyst --category ranking

# Dry-run: validate config + ground truth without calling Snowflake
python agent/run_evals.py --agent tpch-analyst --dry-run
```

## Adding a New Agent

1. Create a folder under `agent/agents/`:

   ```bash
   mkdir -p agent/agents/my-agent/specs/v1 agent/agents/my-agent/prompts agent/agents/my-agent/evals/results agent/agents/my-agent/monitoring
   ```

2. Create the required files:

   **`agent.yml`** — identity config:
   ```yaml
   name: MY_AGENT
   fqn: SANDBOX.TPCH.MY_AGENT
   database: SANDBOX
   schema: TPCH
   description: "What this agent does."
   owner: your-team
   ```

   **`specs/v1/agent_spec.json`** — spec (tools, model, tool_resources):
   ```json
   {
     "models": { "orchestration": "auto" },
     "instructions": {},
     "tools": []
   }
   ```

   **`specs/v1/metadata.yml`** — version info:
   ```yaml
   version: "1.0.0"
   status: "draft"
   agent_name: "MY_AGENT"
   fqn: "SANDBOX.TPCH.MY_AGENT"
   changelog:
     - "Initial spec"
   ```

   **`prompts/orchestration.md`** and **`prompts/response.md`** — system prompts.

   **`evals/eval_config.yaml`** — copy from `tpch-analyst/evals/eval_config.yaml` and update `agent.fqn`, `results.output_dir`, and `results.table`.

   **`evals/ground_truth.json`** — at least 6 Q&A pairs.

3. Deploy and validate:
   ```bash
   python agent/deploy_all.py --dry-run --agent my-agent
   python agent/run_evals.py --agent my-agent --dry-run
   ```

The new agent is automatically picked up by CI on the next push to `main`.

## Versioning a Spec

1. Copy `specs/v1/` → `specs/v2/`, modify `agent_spec.json`.
2. Set `status: draft` in `metadata.yml` and add a changelog entry.
3. Test: `python agent/deploy_all.py --dry-run --agent <name>`
4. Open a PR — CI validates all agents automatically.
5. After merge, CI deploys all agents including the new version.

`scripts/deploy_agent.py` auto-selects the highest `vN` directory with an `agent_spec.json`. To pin a version: `--spec-version v1`.

## CI/CD

| Workflow | Trigger | What runs |
|----------|---------|-----------|
| `validate.yml` | PR to `main` | Required file checks, deploy dry-run for all agents, eval dry-run for all agents |
| `deploy.yml` | Push to `main` | `deploy_all.py` deploys all agents, `run_evals.py --all` runs all eval suites |
