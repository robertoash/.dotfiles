#!/usr/bin/python3

import argparse
import os
import subprocess
import sys
from pathlib import Path

scripts_dir = Path("/home/rash/.config/scripts")
backup_scripts_dir = scripts_dir / "backup" / "crontab"

script_mapping = {
    "proxmox": "bkup_proxmox.py",
    "oldhp": "bkup_oldhp.py",
    "buku": "bkup_buku.py",
    "snapshot-keep": "snapshot_keep_policy.py",
    "take-root-snapshot": "take_root_snapshot.py",
    "take-home-snapshot": "take_home_snapshot.py",
    "take-all-snapshots": "all",
}

additional_args = {
    "take-root-snapshot": [
        "-s",
        f"backup_root_{subprocess.check_output(['date', '+%Y%m%d_%H%M']).decode().strip()}",
    ],
    "take-home-snapshot": [
        "-s",
        f"backup_home_{subprocess.check_output(['date', '+%Y%m%d_%H%M']).decode().strip()}",
    ]
}


def set_pythonpath():
    env = os.environ.copy()
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{env['PYTHONPATH']}:{scripts_dir}"
    else:
        env["PYTHONPATH"] = str(scripts_dir)
    return env


def main():
    parser = argparse.ArgumentParser(
        description="Run backup scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available scripts:\n"
        + "\n".join(f"  {k} -> {v}" for k, v in script_mapping.items()),
    )
    parser.add_argument(
        "--script",
        choices=list(script_mapping.keys()),
        required=True,
        help="Script to run",
    )
    args = parser.parse_args()

    # Handle special case for running all snapshots
    if args.script == "take-all-snapshots":
        # Set PYTHONPATH in the environment
        env = set_pythonpath()
        
        # Run root snapshot first
        root_script_path = backup_scripts_dir / script_mapping["take-root-snapshot"]
        print("Taking root snapshot...")
        try:
            subprocess.run(
                [sys.executable, root_script_path, *additional_args.get("take-root-snapshot", [])],
                env=env,
                check=True,
            )
            print("Root snapshot completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error: Root snapshot failed with exit code {e.returncode}", file=sys.stderr)
            sys.exit(e.returncode)
        
        # Run home snapshot second
        home_script_path = backup_scripts_dir / script_mapping["take-home-snapshot"]
        print("Taking home snapshot...")
        try:
            subprocess.run(
                [sys.executable, home_script_path, *additional_args.get("take-home-snapshot", [])],
                env=env,
                check=True,
            )
            print("Home snapshot completed successfully.")
            print("All snapshots completed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error: Home snapshot failed with exit code {e.returncode}", file=sys.stderr)
            sys.exit(e.returncode)
        
        return

    script_path = backup_scripts_dir / script_mapping[args.script]

    if not script_path.exists():
        print(f"Error: Script file not found: {script_path}", file=sys.stderr)
        print(f"Available scripts: {', '.join(script_mapping.keys())}", file=sys.stderr)
        sys.exit(1)

    # Set PYTHONPATH in the environment
    env = set_pythonpath()

    try:
        subprocess.run(
            [sys.executable, script_path, *additional_args.get(args.script, [])],
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: Script failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)


if __name__ == "__main__":
    main()
