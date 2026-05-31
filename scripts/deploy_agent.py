"""
Builds the CREATE OR REPLACE AGENT SQL for a Cortex Agent and writes it to stdout
for piping into `snow sql`.

Each agent lives in agent/agents/<agent-name>/ and must contain:
  - agent.yml          — identity (name, fqn, database, schema)
  - specs/vN/          — versioned spec JSON + metadata
  - prompts/           — orchestration.md and response.md

Usage:
    # Deploy a specific agent (required when multiple agents exist)
    python scripts/deploy_agent.py --agent tpch-analyst | snow sql -c prod --stdin

    # Dry-run: print the SQL without executing
    python scripts/deploy_agent.py --agent tpch-analyst --dry-run

    # Deploy a specific spec version
    python scripts/deploy_agent.py --agent tpch-analyst --spec-version v2 | snow sql -c prod --stdin

    # If only one agent exists in agent/agents/, --agent can be omitted
    python scripts/deploy_agent.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR   = PROJECT_ROOT / "agent" / "agents"


def discover_agents() -> list[Path]:
    return sorted(p.parent for p in AGENTS_DIR.glob("*/agent.yml"))


def resolve_agent_dir(agent_name: str | None) -> Path:
    agents = discover_agents()
    if not agents:
        print(f"ERROR: No agents found in {AGENTS_DIR}.", file=sys.stderr)
        sys.exit(1)

    if agent_name:
        target = AGENTS_DIR / agent_name
        if not target.is_dir() or not (target / "agent.yml").exists():
            print(f"ERROR: Agent '{agent_name}' not found in {AGENTS_DIR}.", file=sys.stderr)
            sys.exit(1)
        return target

    if len(agents) == 1:
        return agents[0]

    names = ", ".join(a.name for a in agents)
    print(f"ERROR: Multiple agents found ({names}). Specify --agent <name>.", file=sys.stderr)
    sys.exit(1)


def resolve_spec_path(agent_dir: Path, spec_version: str | None) -> Path:
    if spec_version:
        path = agent_dir / "specs" / spec_version / "agent_spec.json"
        if not path.exists():
            print(f"ERROR: Spec not found: {path}", file=sys.stderr)
            sys.exit(1)
        return path

    # Auto-detect the latest stable version (highest vN directory)
    spec_dirs = sorted(
        (d for d in (agent_dir / "specs").iterdir() if d.is_dir() and d.name.startswith("v")),
        key=lambda d: int(d.name[1:]) if d.name[1:].isdigit() else 0,
        reverse=True,
    )
    for spec_dir in spec_dirs:
        candidate = spec_dir / "agent_spec.json"
        if candidate.exists():
            return candidate

    print(f"ERROR: No agent_spec.json found in {agent_dir}/specs/", file=sys.stderr)
    sys.exit(1)


def build_sql(agent_dir: Path, spec_version: str | None) -> str:
    agent_cfg  = yaml.safe_load((agent_dir / "agent.yml").read_text())
    spec_path  = resolve_spec_path(agent_dir, spec_version)
    spec       = json.loads(spec_path.read_text())

    spec.setdefault("instructions", {})

    orch_path = agent_dir / "prompts" / "orchestration.md"
    resp_path = agent_dir / "prompts" / "response.md"

    if orch_path.exists():
        spec["instructions"]["orchestration"] = orch_path.read_text().strip()
    if resp_path.exists():
        spec["instructions"]["response"] = resp_path.read_text().strip()

    fqn      = agent_cfg["fqn"]
    spec_json = json.dumps(spec, indent=2)
    return f"CREATE OR REPLACE AGENT {fqn}\nFROM SPECIFICATION $$\n{spec_json}\n$$;"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Cortex Agent deployment SQL")
    parser.add_argument("--agent",        default=None, help="Agent folder name (e.g. tpch-analyst)")
    parser.add_argument("--spec-version", default=None, help="Spec version to deploy (e.g. v2)")
    parser.add_argument("--dry-run",      action="store_true", help="Print SQL without note of execution")
    args = parser.parse_args()

    agent_dir = resolve_agent_dir(args.agent)
    sql = build_sql(agent_dir, args.spec_version)

    if args.dry_run:
        print("-- DRY RUN: SQL that would be executed:")
    print(sql)


if __name__ == "__main__":
    main()
