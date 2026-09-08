terraform {
  required_version = ">= 1.5"

  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 1.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "snowflake" {
  organization_name = var.snowflake_organization_name
  account_name      = var.snowflake_account_name
  role              = "ACCOUNTADMIN"
}

# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------

module "roles" {
  source      = "./modules/roles"
  environment = var.environment
  env_suffix  = var.env_suffix
}

module "users" {
  source      = "./modules/users"
  environment = var.environment
  env_suffix  = var.env_suffix
  roles       = module.roles.role_names
}

module "grants" {
  source      = "./modules/grants"
  environment = var.environment
  env_suffix  = var.env_suffix
  roles       = module.roles.role_names
  databases   = var.databases
  warehouses  = module.account.warehouse_names
}

module "account" {
  source      = "./modules/account"
  environment = var.environment
  env_suffix  = var.env_suffix
}
