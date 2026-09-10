output "storage_integration_name" {
  description = "Name of the S3 storage integration, or empty string when disabled"
  value       = try(snowflake_storage_integration.s3[0].name, "")
}

output "storage_aws_iam_user_arn" {
  description = "Snowflake-side IAM user ARN — paste into the AWS role trust policy"
  value       = try(snowflake_storage_integration.s3[0].storage_aws_iam_user_arn, "")
}

output "storage_aws_external_id" {
  description = "Snowflake-side external ID — paste into the AWS role trust policy condition"
  value       = try(snowflake_storage_integration.s3[0].storage_aws_external_id, "")
}

output "email_notification_name" {
  description = "Name of the email notification integration, or empty string when disabled"
  value       = try(snowflake_email_notification_integration.alerts[0].name, "")
}

output "queue_notification_name" {
  description = "Name of the queue notification integration, or empty string when disabled"
  value       = try(snowflake_notification_integration.queue[0].name, "")
}

output "api_integration_name" {
  description = "Name of the API integration, or empty string when disabled"
  value       = try(snowflake_api_integration.external_functions[0].name, "")
}

output "egress_network_rule_name" {
  description = "Fully qualified egress network rule, or empty string when disabled"
  value       = try(snowflake_network_rule.egress[0].fully_qualified_name, "")
}
