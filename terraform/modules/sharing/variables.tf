variable "environment" {
  type = string
}

variable "env_suffix" {
  type = string
}

variable "enable_share" {
  description = "Create the outbound share and its grants"
  type        = bool
  default     = false
}

variable "share_name" {
  description = "Base name of the share (env_suffix is appended)"
  type        = string
  default     = "TPCH_MARTS_SHARE"
}

variable "consumer_accounts" {
  description = "Consumer account identifiers, e.g. [\"ORG.CONSUMER_ACCOUNT\"]. Empty creates the share with no consumers attached yet."
  type        = list(string)
  default     = []
}

variable "shared_database" {
  description = "Database the share exposes. A share may only span one database."
  type        = string
  default     = ""
}

variable "shared_schema" {
  description = "Schema within shared_database holding the shared objects"
  type        = string
  default     = "TPCH"
}

variable "shared_views" {
  description = "View names to expose. Prefer views over base tables so physical layout stays changeable."
  type        = list(string)
  default     = []
}
