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
    ├── roles/                 # Functional role hierarchy
    ├── users/                 # Service users (RSA key auth)
    ├── grants/                # Role-to-object privilege grants
    └── account/               # Warehouses, resource monitors, network policies
```

## Naming Convention

All objects follow `<OBJECT_NAME><env_suffix>`:

| Environment | Suffix | Example |
|-------------|--------|---------|
| DEV | `_DEV` | `ANALYTICS_WH_DEV`, `DATA_READER_DEV` |
| PROD | _(none)_ | `ANALYTICS_WH`, `DATA_READER` |

## Role Hierarchy

```
ACCOUNTADMIN
└── SYSADMIN
     └── DATA_PLATFORM_ADMIN     (owns databases, schemas)
          ├── DATA_ENGINEER       (DDL + DML on all schemas)
          ├── DATA_SCIENTIST      (read curated + manage ML)
          └── DATA_READER         (select-only on marts)
     └── CI_DEPLOY_ROLE           (deployment automation)
     └── DATA_PLATFORM_OPENFLOW   (Openflow runtime)
     └── MCP_SERVICE_ROLE         (Cortex Code agent)
```

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
