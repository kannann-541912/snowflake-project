# ---------------------------------------------------------------------------
# Account-level integrations
# ---------------------------------------------------------------------------
# Integrations are account-scoped, security-sensitive and grant-bearing, so
# they belong in InfraOps alongside roles and warehouses — not in a pipeline
# step or a hand-run SQL script.
#
# Everything here is DISABLED BY DEFAULT and gated on an enable_* flag. They
# are real resources rather than commented-out blocks so that `terraform
# validate` and `terraform fmt` in CI keep them honest; turning one on is a
# one-line change in the relevant tfvars file.
#
# NOT REPRESENTABLE in Snowflake-Labs/snowflake ~> 1.0 — these have no
# resource type and must stay in SQL:
#   - EXTERNAL ACCESS INTEGRATION  → ingestion/openflow/setup/03_external_access.sql
#   - GIT integration / repository → no provider support
#   - NOTIFICATION ... TYPE=WEBHOOK (Slack) → only queue/email are supported
# The network rule and secret an EAI consumes ARE supported and are managed
# here, so the SQL script is reduced to the CREATE EXTERNAL ACCESS INTEGRATION
# statement itself.
# ---------------------------------------------------------------------------

# --- Storage integration: S3 external stages ---------------------------------
# Referenced by sources/definitions/stages.sql as TPCH_S3_INTEGRATION.

resource "snowflake_storage_integration" "s3" {
  count = var.enable_storage_integration ? 1 : 0

  name                      = "${var.storage_integration_name}${var.env_suffix}"
  type                      = "EXTERNAL_STAGE"
  storage_provider          = "S3"
  storage_aws_role_arn      = var.storage_aws_role_arn
  storage_allowed_locations = var.storage_allowed_locations
  storage_blocked_locations = var.storage_blocked_locations
  enabled                   = true
  comment                   = "S3 external stage integration [${var.environment}]"

  lifecycle {
    precondition {
      condition     = var.storage_aws_role_arn != ""
      error_message = "storage_aws_role_arn must be set when enable_storage_integration is true."
    }
    precondition {
      condition     = length(var.storage_allowed_locations) > 0
      error_message = "storage_allowed_locations must list at least one s3:// prefix when enable_storage_integration is true."
    }
  }
}

# --- Notification integrations ----------------------------------------------
# agent/agents/tpch-analyst/monitoring/alert_policy.yml references
# SLACK_ALERTS_INTEGRATION. Provider ~> 1.0 cannot create a WEBHOOK-type
# integration, so Slack delivery must be created in SQL. Email and cloud
# queue targets are supported and scaffolded here.

resource "snowflake_email_notification_integration" "alerts" {
  count = var.enable_email_notification ? 1 : 0

  name               = "${var.email_notification_name}${var.env_suffix}"
  enabled            = true
  allowed_recipients = var.email_notification_recipients
  comment            = "Email alert delivery for platform and agent alerts [${var.environment}]"

  lifecycle {
    precondition {
      condition     = length(var.email_notification_recipients) > 0
      error_message = "email_notification_recipients must list at least one verified Snowflake user email when enable_email_notification is true."
    }
  }
}

resource "snowflake_notification_integration" "queue" {
  count = var.enable_queue_notification ? 1 : 0

  name                  = "${var.queue_notification_name}${var.env_suffix}"
  notification_provider = var.queue_notification_provider
  enabled               = true
  aws_sns_topic_arn     = var.queue_sns_topic_arn
  aws_sns_role_arn      = var.queue_sns_role_arn
  comment               = "Queue-based notification target [${var.environment}]"

  lifecycle {
    precondition {
      condition     = var.queue_sns_topic_arn != "" && var.queue_sns_role_arn != ""
      error_message = "queue_sns_topic_arn and queue_sns_role_arn must be set when enable_queue_notification is true."
    }
  }
}

# --- API integration: external functions ------------------------------------

resource "snowflake_api_integration" "external_functions" {
  count = var.enable_api_integration ? 1 : 0

  name                 = "${var.api_integration_name}${var.env_suffix}"
  api_provider         = var.api_provider
  api_aws_role_arn     = var.api_aws_role_arn
  api_allowed_prefixes = var.api_allowed_prefixes
  api_blocked_prefixes = var.api_blocked_prefixes
  enabled              = true
  comment              = "External function API gateway integration [${var.environment}]"

  lifecycle {
    precondition {
      condition     = length(var.api_allowed_prefixes) > 0
      error_message = "api_allowed_prefixes must list at least one endpoint prefix when enable_api_integration is true."
    }
  }
}

# --- Egress network rule + secret consumed by the Openflow EAI ---------------
# The EAI itself is created in ingestion/openflow/setup/03_external_access.sql
# because the provider has no resource for it; these are its dependencies.

resource "snowflake_network_rule" "egress" {
  count = var.enable_egress_network_rule ? 1 : 0

  name       = "${var.egress_network_rule_name}${var.env_suffix}"
  database   = var.databases.sandbox
  schema     = var.egress_network_rule_schema
  type       = "HOST_PORT"
  mode       = "EGRESS"
  value_list = var.egress_allowed_hosts
  comment    = "Allowed egress hosts for the Openflow external access integration [${var.environment}]"

  lifecycle {
    precondition {
      condition     = length(var.egress_allowed_hosts) > 0
      error_message = "egress_allowed_hosts must list at least one host:port when enable_egress_network_rule is true."
    }
  }
}
