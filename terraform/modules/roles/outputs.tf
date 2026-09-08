output "role_names" {
  description = "Map of logical role names to actual Snowflake role names"
  value = {
    data_platform_admin    = snowflake_role.data_platform_admin.name
    data_engineer          = snowflake_role.data_engineer.name
    data_scientist         = snowflake_role.data_scientist.name
    data_reader            = snowflake_role.data_reader.name
    ci_deploy_role         = snowflake_role.ci_deploy_role.name
    data_platform_openflow = snowflake_role.data_platform_openflow.name
    mcp_service_role       = snowflake_role.mcp_service_role.name
  }
}
