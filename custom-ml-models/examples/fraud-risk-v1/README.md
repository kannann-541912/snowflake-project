# Example Model: Fraud Risk v1

This example demonstrates a higher-risk model lifecycle with stronger governance controls than the churn example.

## What this example includes

- Completed model spec with high-risk controls (`model_spec.yml`).
- Completed model card with fairness and oversight notes (`model_card.md`).
- Snowflake SQL for approval-first deployment (`snowflake/sql/001_register_and_deploy_model.sql`).
- Release notes with dual-control promotion steps (`release_notes.md`).

## Intended use

Predict transaction fraud risk score (`0.0` to `1.0`) to support analyst review and fraud prevention actions.

## Key differences from medium-risk examples

- Mandatory dual approval before production activation.
- Tighter drift and latency thresholds.
- Explicit human-in-the-loop policy for high-risk decisions.
