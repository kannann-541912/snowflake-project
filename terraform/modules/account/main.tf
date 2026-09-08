# ---------------------------------------------------------------------------
# Account-Level Objects — Warehouses, Resource Monitors, Network Policies
# ---------------------------------------------------------------------------

# --- Warehouses ---

resource "snowflake_warehouse" "analytics_wh" {
  name                = "ANALYTICS_WH${var.env_suffix}"
  warehouse_size      = var.analytics_wh_size
  auto_suspend        = 60
  auto_resume         = true
  initially_suspended = true
  comment             = "Analytics and pipeline warehouse [${var.environment}]"
}

resource "snowflake_warehouse" "compute_wh" {
  name                = "COMPUTE_WH${var.env_suffix}"
  warehouse_size      = var.compute_wh_size
  auto_suspend        = 60
  auto_resume         = true
  initially_suspended = true
  comment             = "General compute and CI/CD warehouse [${var.environment}]"
}

# --- Resource Monitor ---

resource "snowflake_resource_monitor" "data_platform_monitor" {
  name            = "DATA_PLATFORM_MONITOR${var.env_suffix}"
  credit_quota    = var.resource_monitor_credit_quota
  frequency       = "MONTHLY"
  start_timestamp = "IMMEDIATELY"

  notify_triggers = [75, 90, 100]
  suspend_trigger = 100
  suspend_immediate_trigger = 110
}

# --- Network Policy ---

resource "snowflake_network_policy" "data_platform_policy" {
  name    = "DATA_PLATFORM_NETWORK_POLICY${var.env_suffix}"
  comment = "Network policy for data platform access [${var.environment}]"

  allowed_ip_list = [
    "0.0.0.0/0" # Replace with actual CIDR ranges for your org
  ]
}
