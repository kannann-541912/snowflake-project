# ---------------------------------------------------------------------------
# Functional Roles — Snowflake best-practice role hierarchy
# ---------------------------------------------------------------------------
# Hierarchy:
#   ACCOUNTADMIN
#     └─ SYSADMIN
#          └─ DATA_PLATFORM_ADMIN  (owns databases, schemas, integrations)
#               ├─ DATA_ENGINEER   (create/modify tables, tasks, stages, streams)
#               ├─ DATA_SCIENTIST  (read curated + ML schema, create models)
#               └─ DATA_READER     (select-only on curated marts)
#     └─ SECURITYADMIN
#          └─ CI_DEPLOY_ROLE       (deployment service role)
#          └─ DATA_PLATFORM_OPENFLOW (least-privilege for Openflow runtime)
#          └─ MCP_SERVICE_ROLE     (for MCP service user)
# ---------------------------------------------------------------------------

resource "snowflake_role" "data_platform_admin" {
  name    = "DATA_PLATFORM_ADMIN${var.env_suffix}"
  comment = "Owns data platform databases, schemas, and integrations [${var.environment}]"
}

resource "snowflake_role" "data_engineer" {
  name    = "DATA_ENGINEER${var.env_suffix}"
  comment = "Create and modify tables, tasks, stages, streams [${var.environment}]"
}

resource "snowflake_role" "data_scientist" {
  name    = "DATA_SCIENTIST${var.env_suffix}"
  comment = "Read curated data and manage ML models [${var.environment}]"
}

resource "snowflake_role" "data_reader" {
  name    = "DATA_READER${var.env_suffix}"
  comment = "Select-only access on curated marts and views [${var.environment}]"
}

resource "snowflake_role" "ci_deploy_role" {
  name    = "CI_DEPLOY_ROLE${var.env_suffix}"
  comment = "CI/CD deployment service role [${var.environment}]"
}

resource "snowflake_role" "data_platform_openflow" {
  name    = "DATA_PLATFORM_OPENFLOW${var.env_suffix}"
  comment = "Least-privilege role for Openflow SPCS runtime [${var.environment}]"
}

resource "snowflake_role" "mcp_service_role" {
  name    = "MCP_SERVICE_ROLE${var.env_suffix}"
  comment = "Role for MCP service user operations [${var.environment}]"
}

# ---------------------------------------------------------------------------
# Role hierarchy grants (child → parent)
# ---------------------------------------------------------------------------

resource "snowflake_grant_account_role" "engineer_to_admin" {
  role_name        = snowflake_role.data_engineer.name
  parent_role_name = snowflake_role.data_platform_admin.name
}

resource "snowflake_grant_account_role" "scientist_to_admin" {
  role_name        = snowflake_role.data_scientist.name
  parent_role_name = snowflake_role.data_platform_admin.name
}

resource "snowflake_grant_account_role" "reader_to_admin" {
  role_name        = snowflake_role.data_reader.name
  parent_role_name = snowflake_role.data_platform_admin.name
}

resource "snowflake_grant_account_role" "admin_to_sysadmin" {
  role_name        = snowflake_role.data_platform_admin.name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_grant_account_role" "ci_to_sysadmin" {
  role_name        = snowflake_role.ci_deploy_role.name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_grant_account_role" "openflow_to_sysadmin" {
  role_name        = snowflake_role.data_platform_openflow.name
  parent_role_name = "SYSADMIN"
}

resource "snowflake_grant_account_role" "mcp_to_sysadmin" {
  role_name        = snowflake_role.mcp_service_role.name
  parent_role_name = "SYSADMIN"
}
