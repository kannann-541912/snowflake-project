"""
Deploy one or all Cortex Agents in this project.

Each agent lives in agent/agents/<agent-name>/ and must contain agent.yml.
This script discovers all such directories and deploys them via
scripts/deploy_agent.py piped into `snow sql`.

Usage:
    # Deploy all agents
    python agent/deploy_all.py -c prod

    # Deploy a single agent by folder name
    python agent/deploy_all.py -c prod --agent tpch-analyst

    # Dry-run: print deploy SQL without executing
    python agent/deploy_all.py -c prod --dry-run

    # List discovered agents
    python agent/deploy_all.py --list
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR   = PROJECT_ROOT / "agent" / "agents"
DEPLOY_SCRIPT = PROJECT_ROOT / "scripts" / "deploy_agent.py"


def discover_agents() -> list[Path]:
    return sorted(
        p.parent for p in AGENTS_DIR.glob("*/agent.yml")
    )


def deploy_agent(agent_dir: Path, connection: str, dry_run: bool) -> bool:
    agent_name = agent_dir.name
    print(f"\n>>> Deploying {agent_name}  ({agent_dir})")

    build_cmd = ["python", str(DEPLOY_SCRIPT), "--agent", agent_name]
    if dry_run:
        build_cmd.append("--dry-run")
        print(f"    Command: {' '.join(build_cmd)}")
        result = subprocess.run(build_cmd, cwd=PROJECT_ROOT)
        return result.returncode == 0

    snow_cmd = ["snow", "sql", "-c", connection, "--stdin"]
    print(f"    Build:  {' '.join(build_cmd)}")
    print(f"    Deploy: {' '.join(snow_cmd)}")

    build = subprocess.run(build_cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if build.returncode != 0:
        print(f"    [FAILED] deploy_agent.py exited {build.returncode}")
        print(build.stderr)
        return False

    deploy = subprocess.run(snow_cmd, input=build.stdout, text=True, cwd=PROJECT_ROOT)
    if deploy.returncode != 0:
        print(f"    [FAILED] snow sql exited {deploy.returncode}")
        return False

    print(f"    [OK] {agent_name} deployed successfully.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy Cortex Agents to Snowflake")
    parser.add_argument("-c", "--connection", default="default",
                        help="Snowflake CLI connection name (default: default)")
    parser.add_argument("--agent", default=None,
                        help="Deploy a single agent by folder name (e.g. tpch-analyst)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print deploy SQL without executing")
    parser.add_argument("--list", action="store_true",
                        help="List discovered agents and exit")
    args = parser.parse_args()

    agents = discover_agents()

    if not agents:
        print(f"No agents found in {AGENTS_DIR}. Each agent must have an agent.yml.")
        sys.exit(1)

    if args.list:
        print("Discovered agents:")
        for a in agents:
            print(f"  {a.name}  ({a})")
        return

    if args.agent:
        target = AGENTS_DIR / args.agent
        if not target.is_dir() or not (target / "agent.yml").exists():
            print(f"Agent '{args.agent}' not found or missing agent.yml in {AGENTS_DIR}")
            sys.exit(1)
        agents = [target]

    failures: list[str] = []
    for agent_dir in agents:
        if not deploy_agent(agent_dir, args.connection, args.dry_run):
            failures.append(agent_dir.name)

    print(f"\n{'='*60}")
    if failures:
        print(f"FAILED: {len(failures)} agent(s) — {', '.join(failures)}")
        sys.exit(1)
    mode = "(dry-run)" if args.dry_run else ""
    print(f"All {len(agents)} agent(s) deployed successfully. {mode}")


if __name__ == "__main__":
    main()
