output "role_names" {
  description = "Map of logical functional role names to actual Snowflake role names"
  value = {
    data_platform_admin    = snowflake_account_role.data_platform_admin.name
    data_engineer          = snowflake_account_role.data_engineer.name
    data_scientist         = snowflake_account_role.data_scientist.name
    data_reader            = snowflake_account_role.data_reader.name
    ci_deploy_role         = snowflake_account_role.ci_deploy_role.name
    data_platform_openflow = snowflake_account_role.data_platform_openflow.name
    mcp_service_role       = snowflake_account_role.mcp_service_role.name
  }
}

output "access_role_names" {
  description = "Map of logical access role names to actual Snowflake role names — object privileges attach to these, never to functional roles"
  value = {
    sandbox_ro           = snowflake_account_role.ar_sandbox_ro.name
    sandbox_rw           = snowflake_account_role.ar_sandbox_rw.name
    sandbox_admin        = snowflake_account_role.ar_sandbox_admin.name
    ml_prod_ro           = snowflake_account_role.ar_ml_prod_ro.name
    ml_prod_rw           = snowflake_account_role.ar_ml_prod_rw.name
    wh_analytics_usage   = snowflake_account_role.ar_wh_analytics_usage.name
    wh_analytics_operate = snowflake_account_role.ar_wh_analytics_operate.name
    wh_analytics_admin   = snowflake_account_role.ar_wh_analytics_admin.name
    wh_compute_operate   = snowflake_account_role.ar_wh_compute_operate.name
  }
}
