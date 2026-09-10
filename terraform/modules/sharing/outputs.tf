output "share_name" {
  description = "Name of the outbound share, or empty string when disabled"
  value       = try(snowflake_share.outbound[0].name, "")
}

output "shared_view_count" {
  description = "Number of views exposed through the share"
  value       = length(snowflake_grant_privileges_to_share.view_select)
}
