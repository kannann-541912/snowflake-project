# ---------------------------------------------------------------------------
# Two-tier role model — Snowflake best-practice hierarchy
# ---------------------------------------------------------------------------
# Access roles (AR_*) hold object privileges and nothing else. Functional
# roles are business personas holding no direct object privileges — they
# inherit them by being granted access roles. Adding a persona is then a
# matter of composing existing access roles, not duplicating a privilege block.
#
#   AR_SANDBOX_RO    ─┐
#   AR_SANDBOX_RW    ─┼─► DATA_ENGINEER    ─┐
#   AR_SANDBOX_ADMIN ─┤   DATA_SCIENTIST   ─┼─► DATA_PLATFORM_ADMIN ─► SYSADMIN
#   AR_ML_PROD_RW    ─┤   DATA_READER      ─┘
#   AR_WH_*          ─┘
#
#   CI_DEPLOY_ROLE / DATA_PLATFORM_OPENFLOW / MCP_SERVICE_ROLE ─► SYSADMIN
#
# Service roles roll up to SYSADMIN, not SECURITYADMIN: they create and own
# objects, and Snowflake's guidance is that every object-owning custom role
# ultimately reaches SYSADMIN. SECURITYADMIN is for user/role/grant admin.
#
# Functional role NAMES are deliberately unchanged — dbt profiles.yml,
# ingestion/config/pipeline_config.yml and sources/definitions/access.sql all
# reference them by name.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Access roles — object privileges attach here (see modules/grants)
# ---------------------------------------------------------------------------

resource "snowflake_account_role" "ar_sandbox_ro" {
  name    = "AR_SANDBOX_RO${var.env_suffix}"
  comment = "Access role: read-only on the SANDBOX database [${var.environment}]"
}

resource "snowflake_account_role" "ar_sandbox_rw" {
  name    = "AR_SANDBOX_RW${var.env_suffix}"
  comment = "Access role: read-write plus object creation on SANDBOX [${var.environment}]"
}

resource "snowflake_account_role" "ar_sandbox_admin" {
  name    = "AR_SANDBOX_ADMIN${var.env_suffix}"
  comment = "Access role: schema creation and monitoring on SANDBOX [${var.environment}]"
}

resource "snowflake_account_role" "ar_ml_prod_ro" {
  name    = "AR_ML_PROD_RO${var.env_suffix}"
  comment = "Access role: read-only on the ML database [${var.environment}]"
}

resource "snowflake_account_role" "ar_ml_prod_rw" {
  name    = "AR_ML_PROD_RW${var.env_suffix}"
  comment = "Access role: model and feature object creation on the ML database [${var.environment}]"
}

resource "snowflake_account_role" "ar_wh_analytics_usage" {
  name    = "AR_WH_ANALYTICS_USAGE${var.env_suffix}"
  comment = "Access role: USAGE on the analytics warehouse [${var.environment}]"
}

resource "snowflake_account_role" "ar_wh_analytics_operate" {
  name    = "AR_WH_ANALYTICS_OPERATE${var.env_suffix}"
  comment = "Access role: USAGE and OPERATE on the analytics warehouse [${var.environment}]"
}

resource "snowflake_account_role" "ar_wh_analytics_admin" {
  name    = "AR_WH_ANALYTICS_ADMIN${var.env_suffix}"
  comment = "Access role: USAGE, OPERATE and MONITOR on the analytics warehouse [${var.environment}]"
}

resource "snowflake_account_role" "ar_wh_compute_operate" {
  name    = "AR_WH_COMPUTE_OPERATE${var.env_suffix}"
  comment = "Access role: USAGE and OPERATE on the compute warehouse [${var.environment}]"
}

# ---------------------------------------------------------------------------
# Functional roles — business personas, no direct object privileges
# ---------------------------------------------------------------------------

resource "snowflake_account_role" "data_platform_admin" {
  name    = "DATA_PLATFORM_ADMIN${var.env_suffix}"
  comment = "Owns data platform databases, schemas, and integrations [${var.environment}]"
}

resource "snowflake_account_role" "data_engineer" {
  name    = "DATA_ENGINEER${var.env_suffix}"
  comment = "Create and modify tables, tasks, stages, streams [${var.environment}]"
}

resource "snowflake_account_role" "data_scientist" {
  name    = "DATA_SCIENTIST${var.env_suffix}"
  comment = "Read curated data and manage ML models [${var.environment}]"
}

resource "snowflake_account_role" "data_reader" {
  name    = "DATA_READER${var.env_suffix}"
  comment = "Select-only access on curated marts and views [${var.environment}]"
}

resource "snowflake_account_role" "ci_deploy_role" {
  name    = "CI_DEPLOY_ROLE${var.env_suffix}"
  comment = "CI/CD deployment service role [${var.environment}]"
}

resource "snowflake_account_role" "data_platform_openflow" {
  name    = "DATA_PLATFORM_OPENFLOW${var.env_suffix}"
  comment = "Least-privilege role for Openflow SPCS runtime [${var.environment}]"
}

resource "snowflake_account_role" "mcp_service_role" {
  name    = "MCP_SERVICE_ROLE${var.env_suffix}"
  comment = "Role for MCP service user operations [${var.environment}]"
}

# ---------------------------------------------------------------------------
# Access role → functional role grants
# ---------------------------------------------------------------------------
# This map is the single place defining what each persona can do. Each entry
# reads "<access role> is held by <functional role>".

locals {
  access_role_bindings = {
    # DATA_PLATFORM_ADMIN — full control of the platform databases
    admin_sandbox_admin = { ar = snowflake_account_role.ar_sandbox_admin.name, fr = snowflake_account_role.data_platform_admin.name }
    admin_sandbox_rw    = { ar = snowflake_account_role.ar_sandbox_rw.name, fr = snowflake_account_role.data_platform_admin.name }
    admin_wh            = { ar = snowflake_account_role.ar_wh_analytics_admin.name, fr = snowflake_account_role.data_platform_admin.name }

    # DATA_ENGINEER — build and operate pipelines
    engineer_sandbox_rw = { ar = snowflake_account_role.ar_sandbox_rw.name, fr = snowflake_account_role.data_engineer.name }
    engineer_wh         = { ar = snowflake_account_role.ar_wh_analytics_operate.name, fr = snowflake_account_role.data_engineer.name }

    # DATA_SCIENTIST — read curated data, own the ML database
    scientist_sandbox_ro = { ar = snowflake_account_role.ar_sandbox_ro.name, fr = snowflake_account_role.data_scientist.name }
    scientist_ml_rw      = { ar = snowflake_account_role.ar_ml_prod_rw.name, fr = snowflake_account_role.data_scientist.name }
    scientist_wh         = { ar = snowflake_account_role.ar_wh_analytics_usage.name, fr = snowflake_account_role.data_scientist.name }

    # DATA_READER — select-only
    reader_sandbox_ro = { ar = snowflake_account_role.ar_sandbox_ro.name, fr = snowflake_account_role.data_reader.name }
    reader_wh         = { ar = snowflake_account_role.ar_wh_analytics_usage.name, fr = snowflake_account_role.data_reader.name }

    # CI_DEPLOY_ROLE — deploys every layer, so it needs create rights
    ci_sandbox_admin = { ar = snowflake_account_role.ar_sandbox_admin.name, fr = snowflake_account_role.ci_deploy_role.name }
    ci_sandbox_rw    = { ar = snowflake_account_role.ar_sandbox_rw.name, fr = snowflake_account_role.ci_deploy_role.name }
    ci_ml_rw         = { ar = snowflake_account_role.ar_ml_prod_rw.name, fr = snowflake_account_role.ci_deploy_role.name }
    ci_wh            = { ar = snowflake_account_role.ar_wh_compute_operate.name, fr = snowflake_account_role.ci_deploy_role.name }

    # DATA_PLATFORM_OPENFLOW — writes to landing tables
    openflow_sandbox_rw = { ar = snowflake_account_role.ar_sandbox_rw.name, fr = snowflake_account_role.data_platform_openflow.name }
    openflow_wh         = { ar = snowflake_account_role.ar_wh_analytics_usage.name, fr = snowflake_account_role.data_platform_openflow.name }

    # MCP_SERVICE_ROLE — queries curated data on behalf of Cortex Code
    mcp_sandbox_ro = { ar = snowflake_account_role.ar_sandbox_ro.name, fr = snowflake_account_role.mcp_service_role.name }
    mcp_wh         = { ar = snowflake_account_role.ar_wh_compute_operate.name, fr = snowflake_account_role.mcp_service_role.name }
  }
}

resource "snowflake_grant_account_role" "access_to_functional" {
  for_each = local.access_role_bindings

  role_name        = each.value.ar
  parent_role_name = each.value.fr
}

# ---------------------------------------------------------------------------
# Functional role hierarchy (child → parent)
# ---------------------------------------------------------------------------

resource "snowflake_grant_account_role" "engineer_to_admin" {
  role_name        = snowflake_account_role.data_engineer.name
  parent_role_name = snowflake_account_role.data_platform_admin.name
}

resource "snowflake_grant_account_role" "scientist_to_admin" {
  role_name        = snowflake_account_role.data_scientist.name
  parent_role_name = snowflake_account_role.data_platform_admin.name
}

resource "snowflake_grant_account_role" "reader_to_admin" {
  role_name        = snowflake_account_role.data_reader.name
  parent_role_name = snowflake_account_role.data_platform_admin.name
}

resource "snowflake_grant_account_role" "admin_to_sysadmin" {
  role_name        = snowflake_account_role.data_platform_admin.name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_grant_account_role" "ci_to_sysadmin" {
  role_name        = snowflake_account_role.ci_deploy_role.name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_grant_account_role" "openflow_to_sysadmin" {
  role_name        = snowflake_account_role.data_platform_openflow.name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_grant_account_role" "mcp_to_sysadmin" {
  role_name        = snowflake_account_role.mcp_service_role.name
  parent_role_name = "SYSADMIN"
}
