"""
Openflow — Customers Ingestion Flow (programmatic via nipyapi)

Builds the TPCH Customers ingestion flow on a running Openflow NiFi runtime
using the nipyapi library (Apache NiFi Python API).

Flow:
  ListS3 → FetchS3Object → SplitRecord (CSV) → UpdateRecord (normalize)
        → PutSnowflakeStreaming (CUSTOMERS_RAW)
        ├── [failure] → RetryFlowFile (max 3 retries)
        │               ├── [retry]           → back to PutSnowflakeStreaming
        │               └── [retries_exceeded] → PutSnowflakeStreaming (CUSTOMERS_DLQ)

Usage:
    # Point nipyapi at your Openflow SPCS runtime URL
    export OPENFLOW_RUNTIME_URL=https://<runtime-id>.snowflakecomputing.com/nifi
    python ingestion/openflow/flows/customers_flow.py

    # Dry-run: print the flow config without connecting
    python ingestion/openflow/flows/customers_flow.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# nipyapi is the Apache NiFi Python API client.
# Install: pip install nipyapi
try:
    import nipyapi
    from nipyapi import canvas, config as nifi_config
except ImportError:
    print("ERROR: nipyapi is required. Run: pip install nipyapi")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Configuration — read from environment or override here
# ---------------------------------------------------------------------------

RUNTIME_URL = os.getenv("OPENFLOW_RUNTIME_URL", "https://your-runtime.snowflakecomputing.com/nifi")

S3_BUCKET   = os.getenv("S3_BUCKET", "your-data-bucket")
S3_PREFIX   = os.getenv("S3_CUSTOMERS_PREFIX", "customers/")
AWS_REGION  = os.getenv("AWS_REGION", "us-east-1")

# Snowflake connection — Snowflake Managed Token (SPCS default, no credentials needed)
SF_AUTH_STRATEGY = "SNOWFLAKE_MANAGED"
SF_DATABASE      = "SANDBOX"
SF_SCHEMA        = "TPCH_LANDING"
SF_TABLE         = "CUSTOMERS_RAW"
SF_DLQ_TABLE     = "CUSTOMERS_DLQ"
SF_WAREHOUSE     = "ANALYTICS_WH"


# ---------------------------------------------------------------------------
# Flow definition
# ---------------------------------------------------------------------------

FLOW_CONFIG = {
    "name": "TPCH_Customers_Ingestion",
    "comment": "Loads customer CSV files from S3 into SANDBOX.TPCH_LANDING.CUSTOMERS_RAW",
    "processors": [
        {
            "id": "list_s3",
            "type": "org.apache.nifi.processors.aws.s3.ListS3",
            "name": "ListS3 - Customers",
            "properties": {
                "Bucket": S3_BUCKET,
                "Prefix": S3_PREFIX,
                "Region": AWS_REGION,
                "Listing Strategy": "Tracking Timestamps",
                "AWS Credentials Provider Service": "S3CredentialsService",
                "Record Writer": "JsonRecordSetWriter",
            },
            "scheduling": {
                "strategy": "CRON_DRIVEN",
                "period": "0 0 6 * * ?",     # Daily at 06:00 UTC
            },
        },
        {
            "id": "fetch_s3",
            "type": "org.apache.nifi.processors.aws.s3.FetchS3Object",
            "name": "FetchS3Object - Customers",
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
            "name": "UpdateRecord - Normalize Fields",
            "properties": {
                "Record Reader": "JsonTreeReader",
                "Record Writer": "JsonRecordSetWriter",
                # Normalize email to lowercase, trim name
                "/email": "${field.value:toLower():trim()}",
                "/name":  "${field.value:trim()}",
            },
        },
        {
            "id": "put_snowflake",
            "type": "org.apache.nifi.processors.snowflake.PutSnowflakeStreaming",
            "name": "PutSnowflakeStreaming - CUSTOMERS_RAW",
            "properties": {
                "snowflake-connection-provider":   "SnowflakeStreamingConnectionPool",
                "target-table":                    SF_TABLE,
                "target-database":                 SF_DATABASE,
                "target-schema":                   SF_SCHEMA,
            },
        },
        {
            "id": "retry",
            "type": "org.apache.nifi.processors.standard.RetryFlowFile",
            "name": "RetryFlowFile - Customers",
            "properties": {
                "Maximum Retries":     "3",
                "Penalize Retries":    "true",
                "Reuse Mode":          "FAIL_ON_REUSE",
                "Retry Attribute":     "retry.count",
            },
        },
        {
            "id": "dlq",
            "type": "org.apache.nifi.processors.snowflake.PutSnowflakeStreaming",
            "name": "PutSnowflakeStreaming - CUSTOMERS_DLQ",
            "properties": {
                "snowflake-connection-provider":   "SnowflakeStreamingConnectionPool",
                "target-table":                    SF_DLQ_TABLE,
                "target-database":                 SF_DATABASE,
                "target-schema":                   SF_SCHEMA,
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
            "properties": {
                # Uses IAM role attached to SPCS container — no static credentials
                "Credentials Strategy": "INSTANCE_PROFILE",
            },
        },
        {
            "id": "SnowflakeStreamingConnectionPool",
            "type": "org.apache.nifi.processors.snowflake.service.StandardSnowflakeStreamingConnectionPoolService",
            "name": "SnowflakeStreamingConnectionPool",
            "properties": {
                "snowflake-account-identifier": "xna38553.east-us-2.azure",
                # SPCS Snowflake Managed Token — auto-managed, no key-pair needed
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
                "Treat First Line as Header": "true",
                "Date Format":      "yyyy-MM-dd",
                "Timestamp Format": "yyyy-MM-dd HH:mm:ss",
            },
        },
        {
            "id": "JsonRecordSetWriter",
            "type": "org.apache.nifi.json.JsonRecordSetWriter",
            "name": "JsonRecordSetWriter",
            "properties": {
                "Schema Write Strategy": "no-schema",
                "Output Grouping": "Array",
            },
        },
        {
            "id": "JsonTreeReader",
            "type": "org.apache.nifi.json.JsonTreeReader",
            "name": "JsonTreeReader",
            "properties": {
                "Schema Access Strategy": "Infer Schema",
            },
        },
    ],
}


# ---------------------------------------------------------------------------
# Deployment helpers (nipyapi)
# ---------------------------------------------------------------------------

def connect_to_runtime(runtime_url: str) -> None:
    nifi_config.nifi_config.host = f"{runtime_url}/nifi-api"
    # For SPCS, the session token is injected via SPCS environment automatically.
    # For BYOC, set nifi_config.nifi_config.username / password or token here.
    nipyapi.utils.start_logger()


def create_process_group(name: str) -> object:
    root = canvas.get_process_group("root")
    pg = canvas.create_process_group(root, name, location=(100, 100))
    print(f"Created process group: {pg.component.name} (id={pg.id})")
    return pg


def deploy_controller_services(pg: object, services: list[dict]) -> dict[str, object]:
    deployed = {}
    for svc in services:
        cs = canvas.create_controller_service(
            parent_pg=pg,
            service_type=svc["type"],
        )
        canvas.update_controller_service(cs, body={"component": {
            "id": cs.id,
            "name": svc["name"],
            "properties": svc["properties"],
        }})
        canvas.schedule_controller_service(cs, True)
        deployed[svc["id"]] = cs
        print(f"  [CS] {svc['name']}")
    return deployed


def deploy_processors(pg: object, processors: list[dict], position: int = 0) -> dict[str, object]:
    deployed = {}
    for i, proc in enumerate(processors):
        nifi_proc = canvas.create_processor(
            parent_pg=pg,
            processor=canvas.get_processor_type(proc["type"]),
            location=(200 + i * 300, 200),
            name=proc["name"],
            config={
                "properties": proc.get("properties", {}),
                "schedulingPeriod": proc.get("scheduling", {}).get("period", "0 sec"),
                "schedulingStrategy": proc.get("scheduling", {}).get("strategy", "TIMER_DRIVEN"),
                "comments": proc.get("comment", ""),
            },
        )
        deployed[proc["id"]] = nifi_proc
        print(f"  [PROC] {proc['name']}")
    return deployed


def wire_connections(pg: object, connections: list[dict], proc_map: dict) -> None:
    for conn in connections:
        src = proc_map[conn["from"]]
        dst = proc_map[conn["to"]]
        canvas.create_connection(src, dst, [conn["rel"]])
        print(f"  [CONN] {conn['from']} --{conn['rel']}--> {conn['to']}")


def start_flow(proc_map: dict, processors: list[dict]) -> None:
    for proc in processors:
        canvas.schedule_process(proc_map[proc["id"]], True)
    print("Flow started.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy TPCH Customers Openflow flow")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print flow config without connecting to Openflow runtime")
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps(FLOW_CONFIG, indent=2))
        return

    runtime_url = os.environ.get("OPENFLOW_RUNTIME_URL", RUNTIME_URL)
    print(f"Connecting to Openflow runtime: {runtime_url}")
    connect_to_runtime(runtime_url)

    pg = create_process_group(FLOW_CONFIG["name"])

    print("Deploying controller services...")
    deploy_controller_services(pg, FLOW_CONFIG["controller_services"])

    print("Deploying processors...")
    proc_map = deploy_processors(pg, FLOW_CONFIG["processors"])

    print("Wiring connections...")
    wire_connections(pg, FLOW_CONFIG["connections"], proc_map)

    print("Starting flow...")
    start_flow(proc_map, FLOW_CONFIG["processors"])

    print(f"\nFlow '{FLOW_CONFIG['name']}' deployed successfully.")
    print(f"View in Snowsight: Openflow → Runtime canvas → {FLOW_CONFIG['name']}")


if __name__ == "__main__":
    main()
