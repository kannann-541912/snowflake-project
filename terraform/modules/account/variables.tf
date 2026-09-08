variable "environment" {
  type = string
}

variable "env_suffix" {
  type = string
}

variable "analytics_wh_size" {
  description = "Warehouse size for analytics workloads"
  type        = string
  default     = "XSMALL"
}

variable "compute_wh_size" {
  description = "Warehouse size for compute/CI workloads"
  type        = string
  default     = "XSMALL"
}

variable "resource_monitor_credit_quota" {
  description = "Monthly credit quota for the resource monitor"
  type        = number
  default     = 100
}
