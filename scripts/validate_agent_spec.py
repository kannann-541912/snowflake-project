"""
Validates the Cortex Agent specification JSON.
Checks structure, required fields, and tool/resource consistency.
"""

import json
import sys
from pathlib import Path

AGENT_SPEC_PATH = Path("agent/agent_spec.json")
INSTRUCTIONS_PATH = Path("agent/instructions.md")

REQUIRED_TOP_LEVEL_KEYS = {"models", "tools", "tool_resources"}
REQUIRED_TOOL_SPEC_KEYS = {"type", "name", "description"}
VALID_TOOL_TYPES = {
    "cortex_analyst_text_to_sql",
    "cortex_search",
    "function",
}


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


def main():
    if not AGENT_SPEC_PATH.exists():
        print(f"ERROR: {AGENT_SPEC_PATH} not found. Run from project root.")
        sys.exit(1)

    # Parse JSON
    try:
        spec = json.loads(AGENT_SPEC_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {AGENT_SPEC_PATH}: {e}")
        sys.exit(1)

    # Validate structure
    errors = validate_spec(spec)

    # Check instructions file exists (if referenced)
    if not INSTRUCTIONS_PATH.exists():
        errors.append(f"Instructions file not found: {INSTRUCTIONS_PATH}")

    if errors:
        print("AGENT SPEC VALIDATION ERRORS:")
        print()
        for error in errors:
            print(f"  - {error}")
        print(f"\nFound {len(errors)} error(s) in {AGENT_SPEC_PATH}")
        sys.exit(1)
    else:
        print(f"OK: Agent spec is valid ({len(spec['tools'])} tool(s) configured)")
        sys.exit(0)


if __name__ == "__main__":
    main()
