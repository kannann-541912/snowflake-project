"""
Naming convention linter for DCM SQL definitions.
Ensures all Snowflake object names use UPPER_SNAKE_CASE.
"""

import re
import sys
from pathlib import Path

DEFINITIONS_DIR = Path("sources/definitions")

# Matches DEFINE statements at the start of a line (ignores comments).
# Captures: object type + fully qualified name (including Jinja expressions)
DEFINE_PATTERN = re.compile(
    r"^\s*DEFINE\s+(TABLE|VIEW|WAREHOUSE|ROLE|STAGE|SCHEMA|DATABASE)\s+"
    r"([\w.{}]+)",
    re.IGNORECASE | re.MULTILINE,
)

# Valid UPPER_SNAKE_CASE (letters, digits, underscores, starting with a letter)
VALID_SEGMENT = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Strip Jinja expressions from a segment: DATA_READER{{env_suffix}} -> DATA_READER
JINJA_SUFFIX = re.compile(r"\{\{[^}]+\}\}")


def validate_segment(segment: str) -> bool:
    """Check if a name segment is UPPER_SNAKE_CASE, ignoring Jinja templates."""
    # Pure Jinja expression like {{env_suffix}}
    if segment.startswith("{{") and segment.endswith("}}"):
        return True
    # Strip any embedded Jinja (e.g., DATA_READER{{env_suffix}} -> DATA_READER)
    static_part = JINJA_SUFFIX.sub("", segment)
    if not static_part:
        return True
    return bool(VALID_SEGMENT.match(static_part))


def check_file(path: Path) -> list[str]:
    errors = []
    content = path.read_text()

    for match in DEFINE_PATTERN.finditer(content):
        obj_type = match.group(1).upper()
        full_name = match.group(2)

        # Split fully qualified name: DB.SCHEMA.OBJECT
        segments = full_name.split(".")
        for segment in segments:
            if not validate_segment(segment):
                line_num = content[: match.start()].count("\n") + 1
                errors.append(
                    f"  {path}:{line_num} - {obj_type} name segment '{segment}' "
                    f"is not UPPER_SNAKE_CASE (in '{full_name}')"
                )

    return errors


def main():
    if not DEFINITIONS_DIR.exists():
        print(f"ERROR: {DEFINITIONS_DIR} not found. Run from project root.")
        sys.exit(1)

    sql_files = list(DEFINITIONS_DIR.rglob("*.sql"))
    if not sql_files:
        print("No .sql files found in sources/definitions/")
        sys.exit(0)

    all_errors = []
    for path in sorted(sql_files):
        all_errors.extend(check_file(path))

    if all_errors:
        print("NAMING CONVENTION VIOLATIONS:")
        print()
        for error in all_errors:
            print(error)
        print(f"\nFound {len(all_errors)} violation(s). All object names must be UPPER_SNAKE_CASE.")
        sys.exit(1)
    else:
        print(f"OK: All {len(sql_files)} definition files pass naming conventions.")
        sys.exit(0)


if __name__ == "__main__":
    main()
