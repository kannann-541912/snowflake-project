# ---------------------------------------------------------------------------
# Outbound data sharing (provider side)
# ---------------------------------------------------------------------------
# Publishes curated marts from the SANDBOX database to consumer Snowflake
# accounts via a direct share. Disabled by default and gated on enable_share.
#
# Secure-share rules worth knowing before enabling:
#   - A share can only expose objects from ONE database.
#   - Consumers need USAGE on the database and schema, then SELECT on each
#     object. Grants are explicit per object — there is no "all views" grant
#     to a share, so shared_views is an explicit list by design.
#   - Prefer sharing VIEWS over base tables so the physical layout stays
#     free to change without breaking consumers.
#
# NOT REPRESENTABLE in Snowflake-Labs/snowflake ~> 1.0:
#   - LISTING (Marketplace / private listing) has no resource type. Create the
#     listing in Snowsight on top of the share this module produces.
#   - Reader accounts (snowflake_managed_account) are intentionally out of
#     scope here; they carry their own compute and cost-control requirements.
# ---------------------------------------------------------------------------

resource "snowflake_share" "outbound" {
  count = var.enable_share ? 1 : 0

  name     = "${var.share_name}${var.env_suffix}"
  accounts = var.consumer_accounts
  comment  = "Outbound share of curated marts [${var.environment}]"
}

# Consumers need USAGE on the database before anything inside it resolves.
resource "snowflake_grant_privileges_to_share" "database_usage" {
  count = var.enable_share ? 1 : 0

  to_share    = snowflake_share.outbound[0].name
  privileges  = ["USAGE"]
  on_database = var.shared_database
}

resource "snowflake_grant_privileges_to_share" "schema_usage" {
  count = var.enable_share ? 1 : 0

  to_share   = snowflake_share.outbound[0].name
  privileges = ["USAGE"]
  on_schema  = "${var.shared_database}.${var.shared_schema}"
}

# One grant per shared view — a share has no "all objects" grant.
resource "snowflake_grant_privileges_to_share" "view_select" {
  for_each = var.enable_share ? toset(var.shared_views) : toset([])

  to_share   = snowflake_share.outbound[0].name
  privileges = ["SELECT"]
  on_view    = "${var.shared_database}.${var.shared_schema}.${each.value}"
}
