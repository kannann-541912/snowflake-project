"""
Builds the CREATE OR REPLACE AGENT SQL from the agent spec and instructions.
Outputs the SQL to stdout for piping into `snow sql`.

Usage:
    python scripts/deploy_agent.py
    python scripts/deploy_agent.py --dry-run   (just print, don't execute)
"""

import json
import sys
from pathlib import Path

AGENT_SPEC_PATH = Path("agent/agent_spec.json")
INSTRUCTIONS_PATH = Path("agent/instructions.md")

# Agent coordinates
AGENT_DATABASE = "SANDBOX"
AGENT_SCHEMA = "TPCH"
AGENT_NAME = "TPCH_ANALYST"
AGENT_FQN = f"{AGENT_DATABASE}.{AGENT_SCHEMA}.{AGENT_NAME}"


def build_sql() -> str:
    spec = json.loads(AGENT_SPEC_PATH.read_text())

    # Inject instructions from the markdown file
    if INSTRUCTIONS_PATH.exists():
        instructions_text = INSTRUCTIONS_PATH.read_text().strip()
        if "instructions" not in spec:
            spec["instructions"] = {}
        spec["instructions"]["orchestration"] = instructions_text

    spec_json = json.dumps(spec, indent=2)

    sql = f"CREATE OR REPLACE AGENT {AGENT_FQN}\nFROM SPECIFICATION $spec$\n{spec_json}\n$spec$;"
    return sql


def main():
    if not AGENT_SPEC_PATH.exists():
        print(f"ERROR: {AGENT_SPEC_PATH} not found. Run from project root.", file=sys.stderr)
        sys.exit(1)

    sql = build_sql()

    if "--dry-run" in sys.argv:
        print("-- DRY RUN: SQL that would be executed:")
        print(sql)
    else:
        print(sql)


if __name__ == "__main__":
    main()
