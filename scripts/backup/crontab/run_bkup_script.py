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
    "take-snapshot": "take_linuxmini_snapshot.py",
}

additional_args = {
    "take-snapshot": [
        "-s",
        f"backup_{subprocess.check_output(['date', '+%Y%m%d_%H%M']).decode().strip()}",
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
