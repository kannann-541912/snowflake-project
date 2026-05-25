"""
Deploy one or all Streamlit in Snowflake apps in this project.

Each app lives in streamlit/apps/<app-name>/ and must contain a snowflake.yml.
This script discovers all such manifests and deploys them via `snow streamlit deploy`.

Usage:
    # Deploy all apps
    python streamlit/deploy_all.py -c prod

    # Deploy a single app by folder name
    python streamlit/deploy_all.py -c prod --app data-platform

    # Dry-run: print commands without executing
    python streamlit/deploy_all.py -c prod --dry-run

    # List discovered apps without deploying
    python streamlit/deploy_all.py --list
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

APPS_DIR = Path(__file__).parent / "apps"


def discover_apps() -> list[Path]:
    """Return sorted list of app directories that contain a snowflake.yml."""
    return sorted(
        p.parent for p in APPS_DIR.glob("*/snowflake.yml")
    )


def deploy_app(app_dir: Path, connection: str, dry_run: bool) -> bool:
    """
    Deploy a single app from its directory.
    Returns True on success, False on failure.
    """
    cmd = ["snow", "streamlit", "deploy", "--replace", "-c", connection]
    print(f"\n>>> Deploying {app_dir.name}  ({app_dir})")
    print(f"    Command: {' '.join(cmd)}")

    if dry_run:
        print("    [DRY RUN] skipped.")
        return True

    result = subprocess.run(cmd, cwd=app_dir)
    if result.returncode != 0:
        print(f"    [FAILED] {app_dir.name} exited with code {result.returncode}")
        return False

    print(f"    [OK] {app_dir.name} deployed successfully.")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy Streamlit apps to Snowflake")
    parser.add_argument("-c", "--connection", default="default",
                        help="Snowflake CLI connection name (default: default)")
    parser.add_argument("--app", default=None,
                        help="Deploy a single app by folder name (e.g. data-platform)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print deploy commands without executing them")
    parser.add_argument("--list", action="store_true",
                        help="List discovered apps and exit")
    args = parser.parse_args()

    apps = discover_apps()

    if not apps:
        print(f"No apps found in {APPS_DIR}. Each app must have a snowflake.yml.")
        sys.exit(1)

    if args.list:
        print("Discovered apps:")
        for app in apps:
            print(f"  {app.name}  ({app})")
        return

    if args.app:
        target = APPS_DIR / args.app
        if not target.is_dir() or not (target / "snowflake.yml").exists():
            print(f"App '{args.app}' not found or missing snowflake.yml in {APPS_DIR}")
            sys.exit(1)
        apps = [target]

    failures: list[str] = []
    for app_dir in apps:
        success = deploy_app(app_dir, args.connection, args.dry_run)
        if not success:
            failures.append(app_dir.name)

    print(f"\n{'='*60}")
    if failures:
        print(f"FAILED: {len(failures)} app(s) — {', '.join(failures)}")
        sys.exit(1)
    else:
        mode = "(dry-run)" if args.dry_run else ""
        print(f"All {len(apps)} app(s) deployed successfully. {mode}")


if __name__ == "__main__":
    main()
