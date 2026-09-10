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
  source       = "./modules/grants"
  environment  = var.environment
  env_suffix   = var.env_suffix
  access_roles = module.roles.access_role_names
  databases    = var.databases
  warehouses   = module.account.warehouse_names
}

module "account" {
  source      = "./modules/account"
  environment = var.environment
  env_suffix  = var.env_suffix
}

module "integrations" {
  source      = "./modules/integrations"
  environment = var.environment
  env_suffix  = var.env_suffix
  databases   = var.databases

  enable_storage_integration = var.enable_storage_integration
  storage_aws_role_arn       = var.storage_aws_role_arn
  storage_allowed_locations  = var.storage_allowed_locations

  enable_email_notification     = var.enable_email_notification
  email_notification_recipients = var.email_notification_recipients

  enable_queue_notification = var.enable_queue_notification
  queue_sns_topic_arn       = var.queue_sns_topic_arn
  queue_sns_role_arn        = var.queue_sns_role_arn

  enable_api_integration = var.enable_api_integration
  api_aws_role_arn       = var.api_aws_role_arn
  api_allowed_prefixes   = var.api_allowed_prefixes

  enable_egress_network_rule = var.enable_egress_network_rule
  egress_allowed_hosts       = var.egress_allowed_hosts
}

module "sharing" {
  source      = "./modules/sharing"
  environment = var.environment
  env_suffix  = var.env_suffix

  enable_share      = var.enable_share
  consumer_accounts = var.consumer_accounts
  shared_database   = var.databases.sandbox
  shared_views      = var.shared_views
}
