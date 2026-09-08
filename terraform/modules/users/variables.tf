variable "environment" {
  type = string
}

variable "env_suffix" {
  type = string
}

variable "roles" {
  description = "Map of role names from the roles module"
  type        = map(string)
}
