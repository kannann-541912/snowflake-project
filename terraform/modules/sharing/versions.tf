# Provider source is not inherited from the root module — each child module must
# map the local name `snowflake` to its source, or Terraform infers the
# nonexistent `hashicorp/snowflake` and `init` fails.
terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 1.0"
    }
  }
}
