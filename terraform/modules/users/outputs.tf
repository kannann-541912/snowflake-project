output "service_user_names" {
  description = "List of service user names"
  value = [
    snowflake_user.ci_deploy_svc.name,
    snowflake_user.mcp_service_user.name,
    snowflake_user.openflow_svc.name,
  ]
}
