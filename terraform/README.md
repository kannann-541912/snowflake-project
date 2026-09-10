# Terraform — Snowflake IAM & Account Infrastructure

Manages Snowflake users, roles, grants, warehouses, resource monitors, and network policies using Terraform with environment-aware naming.

## Structure

```
terraform/
├── main.tf                    # Provider, backend, module wiring
├── variables.tf               # Global variables (account, environment)
├── outputs.tf                 # Exported role/warehouse names
├── environments/
│   ├── dev.tfvars             # DEV overrides (suffix: _DEV)
│   └── prod.tfvars            # PROD overrides (suffix: empty)
└── modules/
    ├── roles/                 # Access roles + functional roles + hierarchy
    ├── users/                 # Service users (RSA key auth)
    ├── grants/                # Object privileges → access roles
    ├── account/               # Warehouses, resource monitors, network policies
    ├── integrations/          # Storage / notification / API / network rule
    └── sharing/               # Outbound share (provider side)
```

## Naming Convention

All objects follow `<OBJECT_NAME><env_suffix>`:

| Environment | Suffix | Example |
|-------------|--------|---------|
| DEV | `_DEV` | `ANALYTICS_WH_DEV`, `DATA_READER_DEV` |
| PROD | _(none)_ | `ANALYTICS_WH`, `DATA_READER` |

## Role Model

Two tiers. **Access roles** (`AR_*`) hold object privileges and nothing else.
**Functional roles** are business personas holding no direct object privileges —
they inherit them by being granted access roles.

```
ACCOUNTADMIN
└── SYSADMIN
     └── DATA_PLATFORM_ADMIN     ◄── AR_SANDBOX_ADMIN, AR_SANDBOX_RW, AR_WH_ANALYTICS_ADMIN
          ├── DATA_ENGINEER      ◄── AR_SANDBOX_RW, AR_WH_ANALYTICS_OPERATE
          ├── DATA_SCIENTIST     ◄── AR_SANDBOX_RO, AR_ML_PROD_RW, AR_WH_ANALYTICS_USAGE
          └── DATA_READER        ◄── AR_SANDBOX_RO, AR_WH_ANALYTICS_USAGE
     └── CI_DEPLOY_ROLE          ◄── AR_SANDBOX_ADMIN, AR_SANDBOX_RW, AR_ML_PROD_RW, AR_WH_COMPUTE_OPERATE
     └── DATA_PLATFORM_OPENFLOW  ◄── AR_SANDBOX_RW, AR_WH_ANALYTICS_USAGE
     └── MCP_SERVICE_ROLE        ◄── AR_SANDBOX_RO, AR_WH_COMPUTE_OPERATE
```

Access roles available: `AR_SANDBOX_RO`, `AR_SANDBOX_RW`, `AR_SANDBOX_ADMIN`,
`AR_ML_PROD_RO`, `AR_ML_PROD_RW`, `AR_WH_ANALYTICS_USAGE`,
`AR_WH_ANALYTICS_OPERATE`, `AR_WH_ANALYTICS_ADMIN`, `AR_WH_COMPUTE_OPERATE`.

Service roles roll up to `SYSADMIN`, not `SECURITYADMIN`: they create and own
objects, and Snowflake's guidance is that every object-owning custom role
ultimately reaches `SYSADMIN`. `SECURITYADMIN` is for user/role/grant admin.

**To give a persona new access**, add a binding to `local.access_role_bindings`
in [`modules/roles/main.tf`](modules/roles/main.tf) — do not add a grant in
`modules/grants`, which only ever grants to access roles.

Functional role *names* are unchanged from the single-tier model because
`dbt/profiles.yml`, `ingestion/config/pipeline_config.yml` and
`sources/definitions/access.sql` reference them by name.

## Integrations

Account-level integrations live in [`modules/integrations`](modules/integrations)
and are **all disabled by default**, gated on an `enable_*` flag. They are real
resources rather than commented-out blocks so `terraform fmt`/`validate` in CI
keep them honest. Enable one by flipping its flag in `environments/*.tfvars` and
filling in its settings; a resource `precondition` fails the plan if you enable
a flag without its required values.

| Flag | Creates | Notes |
|------|---------|-------|
| `enable_storage_integration` | `TPCH_S3_INTEGRATION` | Referenced by `sources/definitions/stages.sql` |
| `enable_email_notification` | Email notification integration | Alert delivery |
| `enable_queue_notification` | SNS/SQS/Azure/GCP notification integration | Alert delivery |
| `enable_api_integration` | API integration | External functions |
| `enable_egress_network_rule` | Egress network rule | Consumed by the Openflow EAI |

After enabling the storage integration, finish the AWS trust policy with:

```bash
terraform output storage_integration_aws_trust
```

**Not representable in provider `~> 1.0`** — these have no resource type and stay in SQL:

| Object | Where it lives |
|--------|---------------|
| `EXTERNAL ACCESS INTEGRATION` | [`ingestion/openflow/setup/03_external_access.sql`](../ingestion/openflow/setup/03_external_access.sql) |
| `NOTIFICATION ... TYPE = WEBHOOK` (Slack) | Must be created in SQL — only email and queue targets are supported |
| Git integration / repository | No provider support |
| `LISTING` (Marketplace/private) | Create in Snowsight on top of the share |

> `agent/agents/tpch-analyst/monitoring/alert_policy.yml` references
> `SLACK_ALERTS_INTEGRATION`, which nothing currently creates. Either create it
> in SQL as a webhook integration, or repoint the alert policy at the email
> integration this module can create.

## Data Sharing (outbound)

[`modules/sharing`](modules/sharing) publishes curated marts to consumer
Snowflake accounts via a direct share. Disabled by default.

```hcl
enable_share      = true
consumer_accounts = ["ORG.CONSUMER_ACCOUNT"]
shared_views      = ["CUSTOMER_ORDER_SUMMARY"]
```

A share spans exactly one database. Grants are explicit per object — there is
no "all views" grant to a share — so `shared_views` is an explicit list by
design. Prefer sharing views over base tables so the physical layout stays free
to change without breaking consumers.

## Usage

```bash
# Initialize
cd terraform
terraform init

# Plan for DEV
terraform plan -var-file=environments/dev.tfvars

# Apply DEV
terraform apply -var-file=environments/dev.tfvars

# Plan for PROD
terraform plan -var-file=environments/prod.tfvars
```

## Prerequisites

- Terraform >= 1.5
- Snowflake provider `~> 1.0` (Snowflake-Labs/snowflake)
- `ACCOUNTADMIN` role for initial deployment
- RSA key pairs generated for service users (set via `ALTER USER ... SET RSA_PUBLIC_KEY`)
