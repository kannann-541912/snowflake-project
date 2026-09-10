variable "environment" {
  type = string
}

variable "env_suffix" {
  type = string
}

variable "access_roles" {
  description = "Map of access role names from the roles module — all object privileges in this module attach to these, never to functional roles"
  type        = map(string)
}

variable "databases" {
  description = "Map of logical database names to Snowflake database names"
  type = object({
    sandbox = string
    ml_prod = string
  })
}

variable "warehouses" {
  description = "Map of warehouse names from the account module"
  type        = map(string)
}
