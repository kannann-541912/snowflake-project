variable "environment" {
  type = string
}

variable "env_suffix" {
  type = string
}

variable "databases" {
  description = "Map of logical database names to Snowflake database names"
  type = object({
    sandbox = string
    ml_prod = string
  })
}

# --- Storage integration ----------------------------------------------------

variable "enable_storage_integration" {
  description = "Create the S3 storage integration used by sources/definitions/stages.sql"
  type        = bool
  default     = false
}

variable "storage_integration_name" {
  description = "Base name of the storage integration (env_suffix is appended)"
  type        = string
  default     = "TPCH_S3_INTEGRATION"
}

variable "storage_aws_role_arn" {
  description = "IAM role ARN Snowflake assumes to read the bucket. Required when enable_storage_integration is true."
  type        = string
  default     = ""
}

variable "storage_allowed_locations" {
  description = "s3:// prefixes the integration may read, e.g. [\"s3://my-bucket/customers/\"]"
  type        = list(string)
  default     = []
}

variable "storage_blocked_locations" {
  description = "s3:// prefixes explicitly denied"
  type        = list(string)
  default     = []
}

# --- Notification integrations ----------------------------------------------

variable "enable_email_notification" {
  description = "Create an email notification integration for platform and agent alerts"
  type        = bool
  default     = false
}

variable "email_notification_name" {
  description = "Base name of the email notification integration"
  type        = string
  default     = "PLATFORM_EMAIL_ALERTS"
}

variable "email_notification_recipients" {
  description = "Verified Snowflake user emails permitted as recipients"
  type        = list(string)
  default     = []
}

variable "enable_queue_notification" {
  description = "Create a cloud-queue notification integration (SNS/SQS/Azure/GCP)"
  type        = bool
  default     = false
}

variable "queue_notification_name" {
  description = "Base name of the queue notification integration"
  type        = string
  default     = "PLATFORM_QUEUE_ALERTS"
}

variable "queue_notification_provider" {
  description = "Queue provider: AWS_SNS, AWS_SQS, AZURE_STORAGE_QUEUE or GCP_PUBSUB"
  type        = string
  default     = "AWS_SNS"

  validation {
    condition     = contains(["AWS_SNS", "AWS_SQS", "AZURE_STORAGE_QUEUE", "GCP_PUBSUB"], var.queue_notification_provider)
    error_message = "queue_notification_provider must be AWS_SNS, AWS_SQS, AZURE_STORAGE_QUEUE or GCP_PUBSUB."
  }
}

variable "queue_sns_topic_arn" {
  description = "SNS topic ARN alerts are published to"
  type        = string
  default     = ""
}

variable "queue_sns_role_arn" {
  description = "IAM role ARN Snowflake assumes to publish to the topic"
  type        = string
  default     = ""
}

# --- API integration --------------------------------------------------------

variable "enable_api_integration" {
  description = "Create an API integration for Snowflake external functions"
  type        = bool
  default     = false
}

variable "api_integration_name" {
  description = "Base name of the API integration"
  type        = string
  default     = "PLATFORM_API_INTEGRATION"
}

variable "api_provider" {
  description = "API gateway provider: aws_api_gateway, azure_api_management or google_api_gateway"
  type        = string
  default     = "aws_api_gateway"
}

variable "api_aws_role_arn" {
  description = "IAM role ARN Snowflake assumes to invoke the gateway"
  type        = string
  default     = ""
}

variable "api_allowed_prefixes" {
  description = "Endpoint prefixes external functions may call"
  type        = list(string)
  default     = []
}

variable "api_blocked_prefixes" {
  description = "Endpoint prefixes explicitly denied"
  type        = list(string)
  default     = []
}

# --- Egress network rule ----------------------------------------------------

variable "enable_egress_network_rule" {
  description = "Create the egress network rule consumed by the Openflow external access integration"
  type        = bool
  default     = false
}

variable "egress_network_rule_name" {
  description = "Base name of the egress network rule"
  type        = string
  default     = "TPCH_EGRESS_RULE"
}

variable "egress_network_rule_schema" {
  description = "Schema that holds the network rule"
  type        = string
  default     = "TPCH_LANDING"
}

variable "egress_allowed_hosts" {
  description = "host:port values the runtime may reach, e.g. [\"s3.us-east-1.amazonaws.com:443\"]"
  type        = list(string)
  default     = []
}
