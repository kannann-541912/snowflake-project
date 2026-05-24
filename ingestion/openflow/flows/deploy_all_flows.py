"""
Openflow — Deploy All Flows

Deploys both the Customers and Orders ingestion flows to the Openflow
SPCS runtime in a single command.

Usage:
    export OPENFLOW_RUNTIME_URL=https://<runtime-id>.snowflakecomputing.com/nifi
    python ingestion/openflow/flows/deploy_all_flows.py
    python ingestion/openflow/flows/deploy_all_flows.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure repo root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ingestion.openflow.flows.customers_flow import (
    FLOW_CONFIG as CUSTOMERS_FLOW,
    connect_to_runtime,
    create_process_group,
    deploy_controller_services,
    deploy_processors,
    wire_connections,
    start_flow,
)
from ingestion.openflow.flows.orders_flow import FLOW_CONFIG as ORDERS_FLOW

FLOWS = [CUSTOMERS_FLOW, ORDERS_FLOW]


def deploy_flow(flow_config: dict) -> None:
    pg = create_process_group(flow_config["name"])
    print(f"\nDeploying controller services for '{flow_config['name']}'...")
    deploy_controller_services(pg, flow_config["controller_services"])
    print(f"Deploying processors for '{flow_config['name']}'...")
    proc_map = deploy_processors(pg, flow_config["processors"])
    print(f"Wiring connections for '{flow_config['name']}'...")
    wire_connections(pg, flow_config["connections"], proc_map)
    start_flow(proc_map, flow_config["processors"])
    print(f"  '{flow_config['name']}' deployed and started.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy all TPCH Openflow flows")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print flow configs without connecting")
    args = parser.parse_args()

    if args.dry_run:
        import json
        for flow in FLOWS:
            print(f"\n{'='*60}")
            print(f"  Flow: {flow['name']}")
            print(f"{'='*60}")
            print(json.dumps(flow, indent=2))
        return

    runtime_url = os.environ.get(
        "OPENFLOW_RUNTIME_URL",
        "https://your-runtime.snowflakecomputing.com/nifi"
    )

    print(f"Connecting to Openflow runtime: {runtime_url}")
    connect_to_runtime(runtime_url)

    for flow in FLOWS:
        deploy_flow(flow)

    print("\nAll flows deployed successfully.")
    print("View in Snowsight: Openflow → Runtime canvas")


if __name__ == "__main__":
    main()
