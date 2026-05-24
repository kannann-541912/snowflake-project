"""
Openflow — Orders Ingestion Flow (programmatic via nipyapi)

Loads order CSV files from S3 into SANDBOX.TPCH_LANDING.ORDERS_RAW
using PutSnowflakeStreaming (append-only).

Flow:
  ListS3 → FetchS3Object → SplitRecord (CSV) → UpdateRecord (normalize status)
        → PutSnowflakeStreaming (ORDERS_RAW)
        ├── [failure] → RetryFlowFile (max 3 retries)
        │               ├── [retry]           → back to PutSnowflakeStreaming
        │               └── [retries_exceeded] → PutSnowflakeStreaming (ORDERS_DLQ)

Usage:
    export OPENFLOW_RUNTIME_URL=https://<runtime-id>.snowflakecomputing.com/nifi
    python ingestion/openflow/flows/orders_flow.py
    python ingestion/openflow/flows/orders_flow.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import nipyapi
    from nipyapi import canvas, config as nifi_config
except ImportError:
    print("ERROR: nipyapi is required. Run: pip install nipyapi")
    sys.exit(1)

RUNTIME_URL = os.getenv("OPENFLOW_RUNTIME_URL", "https://your-runtime.snowflakecomputing.com/nifi")

S3_BUCKET  = os.getenv("S3_BUCKET", "your-data-bucket")
S3_PREFIX  = os.getenv("S3_ORDERS_PREFIX", "orders/")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

SF_AUTH_STRATEGY = "SNOWFLAKE_MANAGED"
SF_DATABASE      = "SANDBOX"
SF_SCHEMA        = "TPCH_LANDING"
SF_TABLE         = "ORDERS_RAW"
SF_DLQ_TABLE     = "ORDERS_DLQ"

FLOW_CONFIG = {
    "name": "TPCH_Orders_Ingestion",
    "comment": "Loads order CSV files from S3 into SANDBOX.TPCH_LANDING.ORDERS_RAW",
    "processors": [
        {
            "id": "list_s3",
            "type": "org.apache.nifi.processors.aws.s3.ListS3",
            "name": "ListS3 - Orders",
            "properties": {
                "Bucket": S3_BUCKET,
                "Prefix": S3_PREFIX,
                "Region": AWS_REGION,
                "Listing Strategy": "Tracking Timestamps",
                "AWS Credentials Provider Service": "S3CredentialsService",
            },
            "scheduling": {
                "strategy": "CRON_DRIVEN",
                "period": "0 0 0/4 * * ?",   # Every 4 hours
            },
        },
        {
            "id": "fetch_s3",
            "type": "org.apache.nifi.processors.aws.s3.FetchS3Object",
            "name": "FetchS3Object - Orders",
            "properties": {
                "Bucket": S3_BUCKET,
                "Object Key": "${filename}",
                "Region": AWS_REGION,
                "AWS Credentials Provider Service": "S3CredentialsService",
            },
        },
        {
            "id": "convert_record",
            "type": "org.apache.nifi.processors.standard.ConvertRecord",
            "name": "ConvertRecord - CSV to JSON",
            "properties": {
                "Record Reader": "CSVReader",
                "Record Writer": "JsonRecordSetWriter",
            },
        },
        {
            "id": "update_record",
            "type": "org.apache.nifi.processors.standard.UpdateRecord",
            "name": "UpdateRecord - Normalize Status",
            "properties": {
                "Record Reader": "JsonTreeReader",
                "Record Writer": "JsonRecordSetWriter",
                # Uppercase and trim the STATUS field
                "/status": "${field.value:toUpper():trim()}",
            },
        },
        {
            "id": "put_snowflake",
            "type": "org.apache.nifi.processors.snowflake.PutSnowflakeStreaming",
            "name": "PutSnowflakeStreaming - ORDERS_RAW",
            "properties": {
                "snowflake-connection-provider": "SnowflakeStreamingConnectionPool",
                "target-table":    SF_TABLE,
                "target-database": SF_DATABASE,
                "target-schema":   SF_SCHEMA,
            },
        },
        {
            "id": "retry",
            "type": "org.apache.nifi.processors.standard.RetryFlowFile",
            "name": "RetryFlowFile - Orders",
            "properties": {
                "Maximum Retries": "3",
                "Penalize Retries": "true",
                "Reuse Mode": "FAIL_ON_REUSE",
                "Retry Attribute": "retry.count",
            },
        },
        {
            "id": "dlq",
            "type": "org.apache.nifi.processors.snowflake.PutSnowflakeStreaming",
            "name": "PutSnowflakeStreaming - ORDERS_DLQ",
            "properties": {
                "snowflake-connection-provider": "SnowflakeStreamingConnectionPool",
                "target-table":    SF_DLQ_TABLE,
                "target-database": SF_DATABASE,
                "target-schema":   SF_SCHEMA,
            },
        },
    ],
    "connections": [
        {"from": "list_s3",        "rel": "success",          "to": "fetch_s3"},
        {"from": "fetch_s3",       "rel": "success",          "to": "convert_record"},
        {"from": "convert_record", "rel": "success",          "to": "update_record"},
        {"from": "update_record",  "rel": "success",          "to": "put_snowflake"},
        {"from": "put_snowflake",  "rel": "failure",          "to": "retry"},
        {"from": "retry",          "rel": "retry",            "to": "put_snowflake"},
        {"from": "retry",          "rel": "retries_exceeded", "to": "dlq"},
    ],
    "controller_services": [
        {
            "id": "S3CredentialsService",
            "type": "org.apache.nifi.processors.aws.credentials.provider.service.AWSCredentialsProviderControllerService",
            "name": "S3CredentialsService",
            "properties": {"Credentials Strategy": "INSTANCE_PROFILE"},
        },
        {
            "id": "SnowflakeStreamingConnectionPool",
            "type": "org.apache.nifi.processors.snowflake.service.StandardSnowflakeStreamingConnectionPoolService",
            "name": "SnowflakeStreamingConnectionPool",
            "properties": {
                "snowflake-account-identifier": "xna38553.east-us-2.azure",
                "snowflake-authentication-strategy": SF_AUTH_STRATEGY,
            },
        },
        {
            "id": "CSVReader",
            "type": "org.apache.nifi.csv.CSVReader",
            "name": "CSVReader",
            "properties": {
                "Schema Access Strategy": "Infer Schema",
                "First Line is Header": "true",
                "Date Format": "yyyy-MM-dd",
            },
        },
        {
            "id": "JsonRecordSetWriter",
            "type": "org.apache.nifi.json.JsonRecordSetWriter",
            "name": "JsonRecordSetWriter",
            "properties": {"Output Grouping": "Array"},
        },
        {
            "id": "JsonTreeReader",
            "type": "org.apache.nifi.json.JsonTreeReader",
            "name": "JsonTreeReader",
            "properties": {"Schema Access Strategy": "Infer Schema"},
        },
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy TPCH Orders Openflow flow")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps(FLOW_CONFIG, indent=2))
        return

    from ingestion.openflow.flows.customers_flow import (
        connect_to_runtime, create_process_group,
        deploy_controller_services, deploy_processors,
        wire_connections, start_flow,
    )

    runtime_url = os.environ.get("OPENFLOW_RUNTIME_URL", RUNTIME_URL)
    print(f"Connecting to Openflow runtime: {runtime_url}")
    connect_to_runtime(runtime_url)

    pg = create_process_group(FLOW_CONFIG["name"])
    deploy_controller_services(pg, FLOW_CONFIG["controller_services"])
    proc_map = deploy_processors(pg, FLOW_CONFIG["processors"])
    wire_connections(pg, FLOW_CONFIG["connections"], proc_map)
    start_flow(proc_map, FLOW_CONFIG["processors"])

    print(f"\nFlow '{FLOW_CONFIG['name']}' deployed successfully.")


if __name__ == "__main__":
    main()
