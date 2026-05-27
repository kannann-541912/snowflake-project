"""
Snowpark Python Transformations

Runs inside Snowflake's Python runtime using the Snowpark API.
Handles complex transformations that are impractical in pure SQL.

Usage (from Snowflake Task or local):
    snow snowpark execute procedure SANDBOX.TPCH.NORMALIZE_CUSTOMERS()

Or deploy as a Snowflake Python Stored Procedure via:
    python ingestion/snowpark/transforms.py
"""

from __future__ import annotations

import os
import re

from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, lit, regexp_replace, trim, upper, lower, when

# Database name — overridable via environment variable for CI/branch clones
DB = os.getenv("SNOWFLAKE_DATABASE", "SANDBOX")


# ---------------------------------------------------------------------------
# Email normalization
# ---------------------------------------------------------------------------

def normalize_email(session: Session) -> str:
    """
    Stored procedure: normalize email addresses in CUSTOMERS_RAW.
    - Lowercase, trim whitespace, validate format.
    - Returns a summary string.
    """
    df = session.table(f"{DB}.TPCH_LANDING.CUSTOMERS_RAW")

    normalized = df.with_column(
        "EMAIL",
        lower(trim(col("EMAIL"))),
    ).filter(
        col("EMAIL").rlike(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
    )

    # Write normalized rows to a staging table
    normalized.write.mode("overwrite").save_as_table(
        f"{DB}.TPCH_LANDING.CUSTOMERS_NORMALIZED"
    )

    count = normalized.count()
    return f"Normalized {count} customer email records"


# ---------------------------------------------------------------------------
# Order amount parsing
# ---------------------------------------------------------------------------

def parse_order_amounts(session: Session) -> str:
    """
    Stored procedure: parse TOTAL_AMOUNT strings to numeric, reject invalid rows.
    Writes clean rows to ORDERS_NORMALIZED and bad rows to ORDERS_REJECTED.
    """
    df = session.table(f"{DB}.TPCH_LANDING.ORDERS_RAW")

    # Strip currency symbols and commas, then cast
    cleaned = df.with_column(
        "TOTAL_AMOUNT_CLEAN",
        regexp_replace(col("TOTAL_AMOUNT"), r"[$,]", ""),
    )

    valid = cleaned.filter(col("TOTAL_AMOUNT_CLEAN").rlike(r"^\d+(\.\d{1,2})?$"))
    rejected = cleaned.filter(~col("TOTAL_AMOUNT_CLEAN").rlike(r"^\d+(\.\d{1,2})?$"))

    valid.write.mode("overwrite").save_as_table(f"{DB}.TPCH_LANDING.ORDERS_NORMALIZED")
    rejected.write.mode("overwrite").save_as_table(f"{DB}.TPCH_LANDING.ORDERS_REJECTED")

    return f"Valid: {valid.count()} | Rejected: {rejected.count()}"


# ---------------------------------------------------------------------------
# Stored procedure registration helper
# ---------------------------------------------------------------------------

def register_procedures(session: Session) -> None:
    """
    Register all transforms as Snowflake Stored Procedures.
    Call once during deployment: python ingestion/snowpark/transforms.py
    """
    session.sproc.register(
        func=normalize_email,
        name=f"{DB}.TPCH.NORMALIZE_CUSTOMERS",
        replace=True,
        is_permanent=True,
        stage_location=f"@{DB}.TPCH_LANDING.SNOWPARK_OUTPUT_STAGE",
        packages=["snowflake-snowpark-python"],
        comment="Normalize customer email addresses in landing table",
    )

    session.sproc.register(
        func=parse_order_amounts,
        name=f"{DB}.TPCH.PARSE_ORDER_AMOUNTS",
        replace=True,
        is_permanent=True,
        stage_location=f"@{DB}.TPCH_LANDING.SNOWPARK_OUTPUT_STAGE",
        packages=["snowflake-snowpark-python"],
        comment="Parse and validate order amount strings in landing table",
    )

    print("Stored procedures registered successfully.")


# ---------------------------------------------------------------------------
# Local entrypoint (for development and CI dry-run)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    database = os.getenv("SNOWFLAKE_DATABASE", "SANDBOX")

    connection_params = {
        "account":   os.environ.get("SNOWFLAKE_ACCOUNT", "xna38553.east-us-2.azure"),
        "user":      os.environ.get("SNOWFLAKE_USER", "MCP_SERVICE_USER"),
        "role":      os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "ANALYTICS_WH"),
        "database":  database,
        "schema":    "TPCH",
    }

    # Auth: Programmatic Access Token (PAT) — preferred
    pat = os.getenv("SNOWFLAKE_PAT")
    if pat:
        connection_params["authenticator"] = "programmatic_access_token"
        connection_params["token"] = pat
    else:
        # Fall back to key-pair if PAT not set
        private_key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
        if private_key_path:
            connection_params["private_key_file"] = private_key_path
        else:
            raise ValueError("Set SNOWFLAKE_PAT or SNOWFLAKE_PRIVATE_KEY_PATH")

    with Session.builder.configs(connection_params).create() as session:
        register_procedures(session)
