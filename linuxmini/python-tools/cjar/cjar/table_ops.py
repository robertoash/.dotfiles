#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path
import yaml
import tempfile
import shutil
import secrets
import json

DEFAULT_PANTRY = Path.home() / ".config" / "cjar" / "plates" / "vanilla" / "pantry"
DEFAULT_TABLE_CONFIG = DEFAULT_PANTRY / "table.yml"


def get_table_dirs(table_setup):
    """Extract ingredient locations from recipe."""
    dirs = []

    with open(table_setup, "r") as f:
        data = yaml.safe_load(f)

    for service_name, service in data.get("services", {}).items():
        volumes = service.get("volumes", [])
        for volume in volumes:
            if isinstance(volume, str) and ":" in volume:
                host_path = volume.split(":")[0]
                # Skip system paths like /etc/localtime
                if host_path.startswith("/etc/"):
                    continue
                # Handle ~ paths
                elif host_path.startswith("~"):
                    abs_path = Path(host_path).expanduser()
                    # Only add pantry paths (not plates)
                    if "pantry" in str(abs_path):
                        dirs.append(abs_path)
                elif host_path.startswith("./"):
                    abs_path = table_setup.parent / host_path[2:]
                    dirs.append(abs_path)
                elif not host_path.startswith("/"):
                    abs_path = table_setup.parent / host_path
                    dirs.append(abs_path)

    return dirs


def table_up(table_setup=None):
    table_setup = Path(table_setup) if table_setup else DEFAULT_TABLE_CONFIG

    # Check if the vanilla cookie has been eaten
    if not DEFAULT_PANTRY.exists():
        print("❌ Vanilla cookie not eaten. Run 'cjar eat vanilla' first.")
        sys.exit(1)

    if not table_setup.exists():
        print(f"❌ Table setup not found: {table_setup}")
        print(f"💡 Create your table.yml at {table_setup}")
        sys.exit(1)

    print(f"🍽️  Setting the table with {table_setup}...")

    dirs = get_table_dirs(table_setup)

    for dir_path in dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"🥘 Created fresh ingredient: {dir_path}")

    print("🚀 Preparing the feast...")
    result = subprocess.run(
        ["docker", "compose", "-f", str(table_setup), "up", "-d"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"❌ Failed to set the table: {result.stderr}")
        sys.exit(1)

    print("✅ Table is set! Feast is ready.")
    print(result.stdout)


def table_down(table_setup=None):
    table_setup = Path(table_setup) if table_setup else DEFAULT_TABLE_CONFIG

    if not table_setup.exists():
        print(f"❌ Table setup not found: {table_setup}")
        sys.exit(1)

    print(f"🧹 Clearing the table with {table_setup}...")

    print("🛑 Cleaning up the feast...")
    result = subprocess.run(
        ["docker", "compose", "-f", str(table_setup), "down"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"❌ Failed to clear the table: {result.stderr}")
        sys.exit(1)
    else:
        print(result.stdout)

    print("✅ Table cleared!")


def get_kitchen_status():
    """Peek into the kitchen to see what's cooking"""
    print("👁️  Peeking into the kitchen...")
    print()

    # Check if the vanilla cookie is being enjoyed
    if DEFAULT_PANTRY.exists():
        pantry_items = list(DEFAULT_PANTRY.iterdir()) if DEFAULT_PANTRY.exists() else []
        if pantry_items:
            print(f"🔓 Pantry: Accessible ({len(pantry_items)} ingredients found)")
        else:
            print("📦 Pantry: Empty cabinet (no ingredients found)")
    else:
        print("🔒 Pantry: Locked away (vanilla cookie not eaten)")

    # Survey the table
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "name=stash",
                "--format",
                "{{.Status}}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stdout.strip():
            status = result.stdout.strip()
            if "Up" in status:
                print("🍽️  Table: Set and ready for the feast")
            else:
                print("🍽️  Table: No table set")
        else:
            print("🍽️  Table: No table set")

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("🤷 Table: Can't peek (kitchen door locked)")

    # Check for any mounted cookies
    try:
        from .cookie_ops import get_all_cookies, DINNER_TABLE

        all_cookies = get_all_cookies()

        if all_cookies:
            # Check which cookies are actually mounted (plates have contents)
            served_cookies = []
            for cookie in all_cookies:
                plate_path = DINNER_TABLE / cookie
                if plate_path.exists() and any(plate_path.iterdir()):
                    served_cookies.append(cookie)

            if served_cookies:
                print(f"🍪 Cookies: {len(served_cookies)} currently being enjoyed")
                for cookie in served_cookies[:3]:  # Show first 3
                    print(f"   🍴 {cookie}")
                if len(served_cookies) > 3:
                    print(f"   ... and {len(served_cookies) - 3} more on plates")
            else:
                print(f"🍪 Cookies: {len(all_cookies)} baked but none served")
        else:
            print("🍪 Cookies: Empty jar (no cookies baked)")

    except Exception:
        print("🍪 Cookies: Can't see the jar (something's amiss)")

    print()
    print("👁️  Kitchen inspection complete. Return to your duties.")
