"""
Validates Cortex Agent specification JSON files.
Checks structure, required fields, and tool/resource consistency.

Each agent lives in agent/agents/<agent-name>/ and its specs in specs/vN/agent_spec.json.
Every spec version found is validated — a broken draft fails the check.

Usage:
    # Validate every spec version of every agent (CI default)
    python scripts/validate_agent_spec.py

    # Validate a single agent
    python scripts/validate_agent_spec.py --agent tpch-analyst

    # Validate one specific spec version
    python scripts/validate_agent_spec.py --agent tpch-analyst --spec-version v2

    # Validate only the version that would actually be deployed
    python scripts/validate_agent_spec.py --latest-only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR   = PROJECT_ROOT / "agent" / "agents"

REQUIRED_TOP_LEVEL_KEYS = {"models", "tools", "tool_resources"}
REQUIRED_TOOL_SPEC_KEYS = {"type", "name", "description"}
VALID_TOOL_TYPES = {
    "cortex_analyst_text_to_sql",
    "cortex_search",
    "function",
}


def discover_agents() -> list[Path]:
    return sorted(p.parent for p in AGENTS_DIR.glob("*/agent.yml"))


def resolve_agent_dirs(agent_name: str | None) -> list[Path]:
    agents = discover_agents()
    if not agents:
        print(f"ERROR: No agents found in {AGENTS_DIR}.", file=sys.stderr)
        sys.exit(1)

    if agent_name:
        target = AGENTS_DIR / agent_name
        if not target.is_dir() or not (target / "agent.yml").exists():
            print(f"ERROR: Agent '{agent_name}' not found in {AGENTS_DIR}.", file=sys.stderr)
            sys.exit(1)
        return [target]

    return agents


def resolve_spec_paths(
    agent_dir: Path, spec_version: str | None, latest_only: bool
) -> list[Path]:
    specs_dir = agent_dir / "specs"

    if spec_version:
        path = specs_dir / spec_version / "agent_spec.json"
        if not path.exists():
            print(f"ERROR: Spec not found: {path}", file=sys.stderr)
            sys.exit(1)
        return [path]

    if not specs_dir.is_dir():
        return []

    # Highest vN first — mirrors deploy_agent.resolve_spec_path()
    spec_dirs = sorted(
        (d for d in specs_dir.iterdir() if d.is_dir() and d.name.startswith("v")),
        key=lambda d: int(d.name[1:]) if d.name[1:].isdigit() else 0,
        reverse=True,
    )
    paths = [d / "agent_spec.json" for d in spec_dirs if (d / "agent_spec.json").exists()]
    return paths[:1] if latest_only else paths


def validate_spec(spec: dict) -> list[str]:
    errors = []

    # Check top-level keys
    missing_keys = REQUIRED_TOP_LEVEL_KEYS - set(spec.keys())
    if missing_keys:
        errors.append(f"Missing required top-level keys: {sorted(missing_keys)}")
        return errors  # Can't continue without these

    # Validate models
    models = spec["models"]
    if not isinstance(models, dict):
        errors.append("'models' must be an object")
    elif "orchestration" not in models:
        errors.append("'models' must contain 'orchestration' key")

    # Validate tools array
    tools = spec["tools"]
    if not isinstance(tools, list):
        errors.append("'tools' must be an array")
        return errors

    if len(tools) == 0:
        errors.append("'tools' must contain at least one tool")

    tool_names = set()
    for i, tool in enumerate(tools):
        if "tool_spec" not in tool:
            errors.append(f"tools[{i}]: missing 'tool_spec'")
            continue

        tool_spec = tool["tool_spec"]
        missing = REQUIRED_TOOL_SPEC_KEYS - set(tool_spec.keys())
        if missing:
            errors.append(f"tools[{i}].tool_spec: missing keys {sorted(missing)}")
            continue

        name = tool_spec["name"]
        tool_names.add(name)

        if tool_spec["type"] not in VALID_TOOL_TYPES:
            errors.append(
                f"tools[{i}] '{name}': invalid type '{tool_spec['type']}'. "
                f"Must be one of: {sorted(VALID_TOOL_TYPES)}"
            )

        if not name.replace("_", "").isalnum():
            errors.append(
                f"tools[{i}] '{name}': name must be alphanumeric with underscores only"
            )

        if not tool_spec["description"].strip():
            errors.append(f"tools[{i}] '{name}': description must not be empty")

    # Validate tool_resources
    tool_resources = spec["tool_resources"]
    if not isinstance(tool_resources, dict):
        errors.append("'tool_resources' must be an object")
        return errors

    # Check every tool has a matching resource
    for name in tool_names:
        if name not in tool_resources:
            errors.append(
                f"Tool '{name}' defined in 'tools' but missing from 'tool_resources'"
            )

    # Check no orphan resources
    for name in tool_resources:
        if name not in tool_names:
            errors.append(
                f"Resource '{name}' in 'tool_resources' has no matching tool in 'tools'"
            )

    # Validate each resource entry
    for name, resource in tool_resources.items():
        if not isinstance(resource, dict):
            errors.append(f"tool_resources.{name}: must be an object")
            continue

        # Check for semantic_view or cortex_search_service
        has_sv = "semantic_view" in resource
        has_css = "cortex_search_service" in resource
        has_func = "function" in resource

        if not (has_sv or has_css or has_func):
            errors.append(
                f"tool_resources.{name}: must have 'semantic_view', "
                "'cortex_search_service', or 'function'"
            )

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Cortex Agent spec JSON")
    parser.add_argument("--agent",        default=None, help="Agent folder name (default: all agents)")
    parser.add_argument("--spec-version", default=None, help="Validate only this version (e.g. v2)")
    parser.add_argument("--latest-only",  action="store_true", help="Validate only the version that would be deployed")
    args = parser.parse_args()

    agent_dirs = resolve_agent_dirs(args.agent)

    total_errors = 0
    checked = 0

    for agent_dir in agent_dirs:
        spec_paths = resolve_spec_paths(agent_dir, args.spec_version, args.latest_only)

        if not spec_paths:
            print(f"ERROR: No agent_spec.json found in {agent_dir.name}/specs/", file=sys.stderr)
            total_errors += 1
            continue

        # Prompts are optional in deploy_agent.py, but a spec with empty instructions
        # and no prompt files deploys an agent with no guidance — worth flagging.
        for prompt in ("orchestration.md", "response.md"):
            if not (agent_dir / "prompts" / prompt).exists():
                print(f"WARNING: {agent_dir.name}/prompts/{prompt} not found")

        for spec_path in spec_paths:
            rel = spec_path.relative_to(PROJECT_ROOT)
            checked += 1

            try:
                spec = json.loads(spec_path.read_text())
            except json.JSONDecodeError as e:
                print(f"FAIL {rel}: invalid JSON: {e}", file=sys.stderr)
                total_errors += 1
                continue

            errors = validate_spec(spec)
            if errors:
                print(f"FAIL {rel}", file=sys.stderr)
                for error in errors:
                    print(f"  - {error}", file=sys.stderr)
                total_errors += len(errors)
            else:
                print(f"OK   {rel} ({len(spec['tools'])} tool(s))")

    if total_errors:
        print(f"\nFound {total_errors} error(s) across {checked} spec(s)", file=sys.stderr)
        sys.exit(1)

    print(f"\nAll {checked} spec(s) valid.")


if __name__ == "__main__":
    main()
