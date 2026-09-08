output "role_names" {
  description = "Map of logical role names to actual Snowflake role names"
  value       = module.roles.role_names
}

output "warehouse_names" {
  description = "Map of logical warehouse names to actual Snowflake warehouse names"
  value       = module.account.warehouse_names
}

output "service_users" {
  description = "List of service user names created"
  value       = module.users.service_user_names
}

output "environment" {
  description = "Active deployment environment"
  value       = var.environment
}
