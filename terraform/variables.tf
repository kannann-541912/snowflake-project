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
# Naming Convention
# ---------------------------------------------------------------------------
# All objects follow: <OBJECT_NAME><env_suffix>
#   DEV  → ANALYTICS_WH_DEV, DATA_READER_DEV
#   PROD → ANALYTICS_WH,     DATA_READER
# ---------------------------------------------------------------------------
