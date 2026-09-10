# ---------------------------------------------------------------------------
# Global Variables
# ---------------------------------------------------------------------------

variable "snowflake_organization_name" {
  description = "Snowflake organization name"
  type        = string
}

variable "snowflake_account_name" {
  description = "Snowflake account name"
  type        = string
}

variable "environment" {
  description = "Deployment environment: DEV or PROD"
  type        = string
  validation {
    condition     = contains(["DEV", "PROD"], var.environment)
    error_message = "environment must be DEV or PROD."
  }
}

variable "env_suffix" {
  description = "Naming suffix derived from environment (_DEV for DEV, empty for PROD)"
  type        = string
}

variable "databases" {
  description = "Map of logical database names to their full Snowflake names (environment-aware)"
  type = object({
    sandbox = string
    ml_prod = string
  })
}

# ---------------------------------------------------------------------------
# Integrations — all disabled by default
# ---------------------------------------------------------------------------
# These carry defaults so they need not appear in every tfvars file. Enabling
# one without its required settings fails at plan time via a resource
# precondition rather than erroring against Snowflake.

variable "enable_storage_integration" {
  description = "Create the S3 storage integration referenced by sources/definitions/stages.sql"
  type        = bool
  default     = false
}

variable "storage_aws_role_arn" {
  description = "IAM role ARN Snowflake assumes to read the source bucket"
  type        = string
  default     = ""
}

variable "storage_allowed_locations" {
  description = "s3:// prefixes the storage integration may read"
  type        = list(string)
  default     = []
}

variable "enable_email_notification" {
  description = "Create an email notification integration for platform and agent alerts"
  type        = bool
  default     = false
}

variable "email_notification_recipients" {
  description = "Verified Snowflake user emails permitted as alert recipients"
  type        = list(string)
  default     = []
}

variable "enable_queue_notification" {
  description = "Create a cloud-queue notification integration"
  type        = bool
  default     = false
}

variable "queue_sns_topic_arn" {
  description = "SNS topic ARN alerts are published to"
  type        = string
  default     = ""
}

variable "queue_sns_role_arn" {
  description = "IAM role ARN Snowflake assumes to publish to the SNS topic"
  type        = string
  default     = ""
}

variable "enable_api_integration" {
  description = "Create an API integration for external functions"
  type        = bool
  default     = false
}

variable "api_aws_role_arn" {
  description = "IAM role ARN Snowflake assumes to invoke the API gateway"
  type        = string
  default     = ""
}

variable "api_allowed_prefixes" {
  description = "Endpoint prefixes external functions may call"
  type        = list(string)
  default     = []
}

variable "enable_egress_network_rule" {
  description = "Create the egress network rule consumed by the Openflow external access integration"
  type        = bool
  default     = false
}

variable "egress_allowed_hosts" {
  description = "host:port values the Openflow runtime may reach"
  type        = list(string)
  default     = []
}

# ---------------------------------------------------------------------------
# Outbound data sharing — disabled by default
# ---------------------------------------------------------------------------

variable "enable_share" {
  description = "Create the outbound share exposing curated marts to consumer accounts"
  type        = bool
  default     = false
}

variable "consumer_accounts" {
  description = "Consumer account identifiers the share is offered to"
  type        = list(string)
  default     = []
}

variable "shared_views" {
  description = "View names exposed through the share"
  type        = list(string)
  default     = []
}

# ---------------------------------------------------------------------------
# Naming Convention
# ---------------------------------------------------------------------------
# All objects follow: <OBJECT_NAME><env_suffix>
#   DEV  → ANALYTICS_WH_DEV, DATA_READER_DEV
#   PROD → ANALYTICS_WH,     DATA_READER
# ---------------------------------------------------------------------------
