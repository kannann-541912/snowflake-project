# Agent Spec Versioning

Each subdirectory represents a released version of the Cortex Agent spec.

## Directory Layout

```
specs/
├── v1/
│   ├── agent_spec.json   # Versioned spec snapshot
│   └── metadata.yml      # Version metadata, changelog, status
└── v2/                   # Future versions added here
```

## Versioning Policy

| Field | Rule |
|-------|------|
| Version bump | Any change to tools, models, or tool_resources requires a new version |
| `status` | `draft` → `stable` → `deprecated` |
| Breaking changes | Must be listed in `metadata.yml` before deployment |
| Rollback | Deploy any prior `agent_spec.json` via `--spec-version vN` |

## Promoting a New Version

1. Create `specs/vN/agent_spec.json` with your changes.
2. Add `specs/vN/metadata.yml` with changelog and `status: draft`.
3. Run evals: `python agent/run_evals.py --agent retail-category-analytics`
4. If evals pass, set `status: stable` and open a PR.
5. After merge, CI deploys via `deploy_all.py`.
