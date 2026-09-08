# ---------------------------------------------------------------------------
# Service Users — RSA key-pair authentication (no passwords)
# ---------------------------------------------------------------------------

resource "snowflake_user" "ci_deploy_svc" {
  name          = "CI_DEPLOY_SVC${var.env_suffix}"
  login_name    = "CI_DEPLOY_SVC${var.env_suffix}"
  comment       = "CI/CD deployment service user [${var.environment}]"
  default_role  = var.roles["ci_deploy_role"]
  disabled      = false
  must_change_password = false
}

resource "snowflake_user" "mcp_service_user" {
  name          = "MCP_SERVICE_USER${var.env_suffix}"
  login_name    = "MCP_SERVICE_USER${var.env_suffix}"
  comment       = "MCP service user for Cortex Code [${var.environment}]"
  default_role  = var.roles["mcp_service_role"]
  disabled      = false
  must_change_password = false
}

resource "snowflake_user" "openflow_svc" {
  name          = "OPENFLOW_SVC${var.env_suffix}"
  login_name    = "OPENFLOW_SVC${var.env_suffix}"
  comment       = "Openflow SPCS runtime service user [${var.environment}]"
  default_role  = var.roles["data_platform_openflow"]
  disabled      = false
  must_change_password = false
}

# ---------------------------------------------------------------------------
# Role assignments to service users
# ---------------------------------------------------------------------------

resource "snowflake_grant_account_role" "ci_role_to_ci_user" {
  role_name = var.roles["ci_deploy_role"]
  user_name = snowflake_user.ci_deploy_svc.name
}

resource "snowflake_grant_account_role" "mcp_role_to_mcp_user" {
  role_name = var.roles["mcp_service_role"]
  user_name = snowflake_user.mcp_service_user.name
}

resource "snowflake_grant_account_role" "openflow_role_to_openflow_user" {
  role_name = var.roles["data_platform_openflow"]
  user_name = snowflake_user.openflow_svc.name
}
