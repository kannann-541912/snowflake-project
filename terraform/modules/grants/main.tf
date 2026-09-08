# ---------------------------------------------------------------------------
# Privilege Grants — maps roles to object-level permissions
# ---------------------------------------------------------------------------

# --- DATA_PLATFORM_ADMIN: full ownership of data platform databases ---

resource "snowflake_grant_privileges_to_account_role" "admin_sandbox_usage" {
  account_role_name = var.roles["data_platform_admin"]
  privileges        = ["USAGE", "MONITOR", "CREATE SCHEMA"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "admin_sandbox_all_schemas" {
  account_role_name = var.roles["data_platform_admin"]
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "CREATE DYNAMIC TABLE", "CREATE TASK", "CREATE STAGE", "CREATE STREAM", "CREATE PIPE", "CREATE FUNCTION", "CREATE PROCEDURE"]
  on_schema {
    all_schemas_in_database = var.databases.sandbox
  }
}

# --- DATA_ENGINEER: create/modify in landing + curated schemas ---

resource "snowflake_grant_privileges_to_account_role" "engineer_db_usage" {
  account_role_name = var.roles["data_engineer"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "engineer_schema_usage" {
  account_role_name = var.roles["data_engineer"]
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "CREATE TASK", "CREATE STREAM", "CREATE STAGE"]
  on_schema {
    all_schemas_in_database = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "engineer_tables" {
  account_role_name = var.roles["data_engineer"]
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_database        = var.databases.sandbox
    }
  }
}

# --- DATA_SCIENTIST: read curated + ML schema ---

resource "snowflake_grant_privileges_to_account_role" "scientist_db_usage" {
  account_role_name = var.roles["data_scientist"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "scientist_select_tables" {
  account_role_name = var.roles["data_scientist"]
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_database        = var.databases.sandbox
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "scientist_ml_db_usage" {
  account_role_name = var.roles["data_scientist"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.ml_prod
  }
}

resource "snowflake_grant_privileges_to_account_role" "scientist_ml_all" {
  account_role_name = var.roles["data_scientist"]
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "CREATE FUNCTION", "CREATE PROCEDURE"]
  on_schema {
    all_schemas_in_database = var.databases.ml_prod
  }
}

# --- DATA_READER: select-only on curated layer ---

resource "snowflake_grant_privileges_to_account_role" "reader_db_usage" {
  account_role_name = var.roles["data_reader"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "reader_schema_usage" {
  account_role_name = var.roles["data_reader"]
  privileges        = ["USAGE"]
  on_schema {
    all_schemas_in_database = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "reader_select_tables" {
  account_role_name = var.roles["data_reader"]
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_database        = var.databases.sandbox
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "reader_select_views" {
  account_role_name = var.roles["data_reader"]
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = "VIEWS"
      in_database        = var.databases.sandbox
    }
  }
}

# --- Warehouse grants ---

resource "snowflake_grant_privileges_to_account_role" "admin_wh_usage" {
  account_role_name = var.roles["data_platform_admin"]
  privileges        = ["USAGE", "OPERATE", "MONITOR"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["analytics_wh"]
  }
}

resource "snowflake_grant_privileges_to_account_role" "engineer_wh_usage" {
  account_role_name = var.roles["data_engineer"]
  privileges        = ["USAGE", "OPERATE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["analytics_wh"]
  }
}

resource "snowflake_grant_privileges_to_account_role" "reader_wh_usage" {
  account_role_name = var.roles["data_reader"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["analytics_wh"]
  }
}

resource "snowflake_grant_privileges_to_account_role" "ci_wh_usage" {
  account_role_name = var.roles["ci_deploy_role"]
  privileges        = ["USAGE", "OPERATE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["compute_wh"]
  }
}

resource "snowflake_grant_privileges_to_account_role" "openflow_wh_usage" {
  account_role_name = var.roles["data_platform_openflow"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["analytics_wh"]
  }
}

resource "snowflake_grant_privileges_to_account_role" "mcp_wh_usage" {
  account_role_name = var.roles["mcp_service_role"]
  privileges        = ["USAGE", "OPERATE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["compute_wh"]
  }
}
