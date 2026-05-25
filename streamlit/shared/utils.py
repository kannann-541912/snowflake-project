"""
Shared utilities for all Streamlit in Snowflake apps in this project.

Import in any app with:
    import sys, pathlib
    sys.path.append(str(pathlib.Path(__file__).parents[2]))
    from shared.utils import get_session, fmt_currency, fmt_number
"""

from __future__ import annotations

import os


def get_session():
    """
    Return a Snowpark session whether running inside Snowflake (SiS)
    or locally via environment variables.

    SiS runtime:   uses get_active_session() — no credentials needed.
    Local testing: uses env vars SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER,
                   SNOWFLAKE_PAT (programmatic access token).
    """
    try:
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    except Exception:
        from snowflake.snowpark import Session
        return Session.builder.configs({
            "account":       os.environ["SNOWFLAKE_ACCOUNT"],
            "user":          os.environ["SNOWFLAKE_USER"],
            "token":         os.environ["SNOWFLAKE_PAT"],
            "authenticator": "oauth",
            "warehouse":     os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
            "database":      os.environ.get("SNOWFLAKE_DATABASE", "SANDBOX"),
            "schema":        os.environ.get("SNOWFLAKE_SCHEMA", "TPCH"),
        }).create()


def fmt_currency(value: float) -> str:
    """Format a float as a USD currency string."""
    return f"${value:,.2f}"


def fmt_number(value: int | float) -> str:
    """Format a number with thousands separator."""
    return f"{value:,.0f}"
