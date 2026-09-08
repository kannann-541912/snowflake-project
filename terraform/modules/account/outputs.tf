output "warehouse_names" {
  description = "Map of logical warehouse names to actual Snowflake names"
  value = {
    analytics_wh = snowflake_warehouse.analytics_wh.name
    compute_wh   = snowflake_warehouse.compute_wh.name
  }
}

output "resource_monitor_name" {
  description = "Name of the resource monitor"
  value       = snowflake_resource_monitor.data_platform_monitor.name
}
