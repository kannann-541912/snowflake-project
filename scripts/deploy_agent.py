"""
Builds the CREATE OR REPLACE AGENT SQL from the agent spec and instructions.
Outputs the SQL to stdout for piping into `snow sql`.

Usage:
    python scripts/deploy_agent.py
    python scripts/deploy_agent.py --dry-run          # Print SQL, don't execute
    python scripts/deploy_agent.py --spec-version v2  # Deploy a versioned spec
"""

import argparse
import json
import sys
from pathlib import Path

INSTRUCTIONS_PATH = Path("agent/instructions.md")
ORCHESTRATION_PROMPT_PATH = Path("agent/prompts/orchestration.md")
RESPONSE_PROMPT_PATH = Path("agent/prompts/response.md")

# Agent coordinates
AGENT_DATABASE = "SANDBOX"
AGENT_SCHEMA = "TPCH"
AGENT_NAME = "TPCH_ANALYST"
AGENT_FQN = f"{AGENT_DATABASE}.{AGENT_SCHEMA}.{AGENT_NAME}"


def resolve_spec_path(spec_version: str | None) -> Path:
    if spec_version:
        versioned = Path(f"agent/specs/{spec_version}/agent_spec.json")
        if not versioned.exists():
            print(f"ERROR: Versioned spec not found: {versioned}", file=sys.stderr)
            sys.exit(1)
        return versioned
    # Default: canonical spec at agent/agent_spec.json
    default = Path("agent/agent_spec.json")
    if not default.exists():
        print(f"ERROR: {default} not found. Run from project root.", file=sys.stderr)
        sys.exit(1)
    return default


def build_sql(spec_version: str | None) -> str:
    spec_path = resolve_spec_path(spec_version)
    spec = json.loads(spec_path.read_text())

    if "instructions" not in spec:
        spec["instructions"] = {}

    # Prefer granular prompt files; fall back to legacy instructions.md
    if ORCHESTRATION_PROMPT_PATH.exists():
        spec["instructions"]["orchestration"] = ORCHESTRATION_PROMPT_PATH.read_text().strip()
    elif INSTRUCTIONS_PATH.exists():
        spec["instructions"]["orchestration"] = INSTRUCTIONS_PATH.read_text().strip()

    if RESPONSE_PROMPT_PATH.exists():
        spec["instructions"]["response"] = RESPONSE_PROMPT_PATH.read_text().strip()

    spec_json = json.dumps(spec, indent=2)
    return f"CREATE OR REPLACE AGENT {AGENT_FQN}\nFROM SPECIFICATION $spec$\n{spec_json}\n$spec$;"


def main():
    parser = argparse.ArgumentParser(description="Generate Cortex Agent deployment SQL")
    parser.add_argument("--dry-run", action="store_true", help="Print SQL without executing")
    parser.add_argument("--spec-version", default=None, help="Spec version to deploy, e.g. v2")
    args = parser.parse_args()

    sql = build_sql(args.spec_version)

    if args.dry_run:
        print("-- DRY RUN: SQL that would be executed:")
    print(sql)


if __name__ == "__main__":
    main()
