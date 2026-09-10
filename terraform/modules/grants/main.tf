# ---------------------------------------------------------------------------
# Privilege Grants — object privileges attach to ACCESS roles only
# ---------------------------------------------------------------------------
# Nothing here grants to a functional role. Personas acquire these privileges
# by inheriting access roles (see modules/roles, local.access_role_bindings).
# To give a persona new access, bind an existing access role there rather than
# adding a grant here.
# ---------------------------------------------------------------------------

# --- AR_SANDBOX_RO: read-only across the SANDBOX database ---

resource "snowflake_grant_privileges_to_account_role" "sandbox_ro_db" {
  account_role_name = var.access_roles["sandbox_ro"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "sandbox_ro_schemas" {
  account_role_name = var.access_roles["sandbox_ro"]
  privileges        = ["USAGE"]
  on_schema {
    all_schemas_in_database = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "sandbox_ro_tables" {
  account_role_name = var.access_roles["sandbox_ro"]
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_database        = var.databases.sandbox
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "sandbox_ro_views" {
  account_role_name = var.access_roles["sandbox_ro"]
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = "VIEWS"
      in_database        = var.databases.sandbox
    }
  }
}

# --- AR_SANDBOX_RW: write plus pipeline object creation ---

resource "snowflake_grant_privileges_to_account_role" "sandbox_rw_db" {
  account_role_name = var.access_roles["sandbox_rw"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "sandbox_rw_schemas" {
  account_role_name = var.access_roles["sandbox_rw"]
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "CREATE TASK", "CREATE STREAM", "CREATE STAGE"]
  on_schema {
    all_schemas_in_database = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "sandbox_rw_tables" {
  account_role_name = var.access_roles["sandbox_rw"]
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_database        = var.databases.sandbox
    }
  }
}

# --- AR_SANDBOX_ADMIN: schema creation and monitoring ---

resource "snowflake_grant_privileges_to_account_role" "sandbox_admin_db" {
  account_role_name = var.access_roles["sandbox_admin"]
  privileges        = ["USAGE", "MONITOR", "CREATE SCHEMA"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.sandbox
  }
}

resource "snowflake_grant_privileges_to_account_role" "sandbox_admin_schemas" {
  account_role_name = var.access_roles["sandbox_admin"]
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "CREATE DYNAMIC TABLE", "CREATE TASK", "CREATE STAGE", "CREATE STREAM", "CREATE PIPE", "CREATE FUNCTION", "CREATE PROCEDURE"]
  on_schema {
    all_schemas_in_database = var.databases.sandbox
  }
}

# --- AR_ML_PROD_RO / AR_ML_PROD_RW: the ML database ---

resource "snowflake_grant_privileges_to_account_role" "ml_ro_db" {
  account_role_name = var.access_roles["ml_prod_ro"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.ml_prod
  }
}

resource "snowflake_grant_privileges_to_account_role" "ml_ro_schemas" {
  account_role_name = var.access_roles["ml_prod_ro"]
  privileges        = ["USAGE"]
  on_schema {
    all_schemas_in_database = var.databases.ml_prod
  }
}

resource "snowflake_grant_privileges_to_account_role" "ml_ro_tables" {
  account_role_name = var.access_roles["ml_prod_ro"]
  privileges        = ["SELECT"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_database        = var.databases.ml_prod
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "ml_rw_db" {
  account_role_name = var.access_roles["ml_prod_rw"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.databases.ml_prod
  }
}

resource "snowflake_grant_privileges_to_account_role" "ml_rw_schemas" {
  account_role_name = var.access_roles["ml_prod_rw"]
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "CREATE FUNCTION", "CREATE PROCEDURE"]
  on_schema {
    all_schemas_in_database = var.databases.ml_prod
  }
}

resource "snowflake_grant_privileges_to_account_role" "ml_rw_tables" {
  account_role_name = var.access_roles["ml_prod_rw"]
  privileges        = ["SELECT", "INSERT", "UPDATE", "DELETE"]
  on_schema_object {
    all {
      object_type_plural = "TABLES"
      in_database        = var.databases.ml_prod
    }
  }
}

# --- Warehouse access roles ---

resource "snowflake_grant_privileges_to_account_role" "wh_analytics_usage" {
  account_role_name = var.access_roles["wh_analytics_usage"]
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["analytics_wh"]
  }
}

resource "snowflake_grant_privileges_to_account_role" "wh_analytics_operate" {
  account_role_name = var.access_roles["wh_analytics_operate"]
  privileges        = ["USAGE", "OPERATE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["analytics_wh"]
  }
}

resource "snowflake_grant_privileges_to_account_role" "wh_analytics_admin" {
  account_role_name = var.access_roles["wh_analytics_admin"]
  privileges        = ["USAGE", "OPERATE", "MONITOR"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["analytics_wh"]
  }
}

resource "snowflake_grant_privileges_to_account_role" "wh_compute_operate" {
  account_role_name = var.access_roles["wh_compute_operate"]
  privileges        = ["USAGE", "OPERATE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouses["compute_wh"]
  }
}
