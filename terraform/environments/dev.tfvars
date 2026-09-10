snowflake_organization_name = "A5701997473071"
snowflake_account_name      = "MPA05784"
environment                 = "DEV"
env_suffix                  = "_DEV"

databases = {
  sandbox = "SANDBOX_DEV"
  ml_prod = "ML_PROD_DEV"
}

# ---------------------------------------------------------------------------
# Integrations — all off. Flip a flag and fill its settings to enable.
# Enabling without the required settings fails at plan time, not against
# Snowflake, via preconditions in modules/integrations.
# ---------------------------------------------------------------------------
enable_storage_integration = false
# storage_aws_role_arn      = "arn:aws:iam::<account-id>:role/<snowflake-role>"
# storage_allowed_locations = ["s3://<bucket>/customers/", "s3://<bucket>/orders/"]

enable_email_notification = false
# email_notification_recipients = ["data-platform@example.com"]

enable_queue_notification = false
# queue_sns_topic_arn = "arn:aws:sns:<region>:<account-id>:<topic>"
# queue_sns_role_arn  = "arn:aws:iam::<account-id>:role/<sns-publish-role>"

enable_api_integration = false
# api_aws_role_arn     = "arn:aws:iam::<account-id>:role/<api-invoke-role>"
# api_allowed_prefixes = ["https://<api-id>.execute-api.<region>.amazonaws.com/"]

enable_egress_network_rule = false
# egress_allowed_hosts = ["s3.<region>.amazonaws.com:443"]

# ---------------------------------------------------------------------------
# Outbound data sharing — off
# ---------------------------------------------------------------------------
enable_share = false
# consumer_accounts = ["<ORG>.<CONSUMER_ACCOUNT>"]
# shared_views      = ["CUSTOMER_ORDER_SUMMARY"]
