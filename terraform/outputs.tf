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

output "access_role_names" {
  description = "Map of logical access role names to actual Snowflake role names"
  value       = module.roles.access_role_names
}

output "environment" {
  description = "Active deployment environment"
  value       = var.environment
}

# --- Integrations (empty strings when the corresponding flag is off) --------

output "integration_names" {
  description = "Names of the account-level integrations that are enabled"
  value = {
    storage      = module.integrations.storage_integration_name
    email_alerts = module.integrations.email_notification_name
    queue_alerts = module.integrations.queue_notification_name
    api          = module.integrations.api_integration_name
    egress_rule  = module.integrations.egress_network_rule_name
  }
}

# Needed to finish the AWS-side trust policy after enabling the storage
# integration: `terraform output storage_integration_aws_trust`.
output "storage_integration_aws_trust" {
  description = "Snowflake IAM user ARN and external ID to place in the AWS role trust policy"
  value = {
    aws_iam_user_arn = module.integrations.storage_aws_iam_user_arn
    external_id      = module.integrations.storage_aws_external_id
  }
}

# --- Data sharing -----------------------------------------------------------

output "share_name" {
  description = "Name of the outbound share, or empty string when disabled"
  value       = module.sharing.share_name
}
