# Example Model: Churn Risk v1

This is a reference implementation showing how to use this repository's ML lifecycle standards for a single model.

## What this example includes

- A completed model spec (`model_spec.yml`).
- A completed model card (`model_card.md`).
- A Snowflake SQL script to register and activate the model version (`snowflake/sql/001_register_model.sql`).
- A simple release checklist tailored to this model (`release_notes.md`).

## Intended use

Predict customer churn risk score (`0.0` to `1.0`) for subscription accounts and support retention workflows.

## How to adapt

1. Copy this folder to a new model name and version.
2. Replace data sources, metrics, owner, and thresholds.
3. Update SQL registration metadata and artifact URI.
4. Run staging validation before production promotion.
