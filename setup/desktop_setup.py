"""
Setup desktop files and launch agents.
"""

import subprocess
from pathlib import Path

from symlink_utils import create_symlink


def setup_desktop_files(dotfiles_dir, hostname, home):
    """Rsync desktop files (Linux only)"""
    machine_dir = dotfiles_dir / hostname
    desktop_files_source = machine_dir / "local" / "share" / "applications"
    desktop_files_target = home / ".local" / "share" / "applications"

    if desktop_files_source.exists():
        print("\n🖥️  Step 7: Syncing desktop files...")
        desktop_files_target.mkdir(parents=True, exist_ok=True)

        # Use rsync to mirror the directory
        result = subprocess.run(
            ["rsync", "-av", "--delete", f"{desktop_files_source}/", f"{desktop_files_target}/"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # Count synced files
            synced_files = [line for line in result.stdout.split("\n") if line.endswith(".desktop")]
            print(f"  ✅ Synced {len(synced_files)} desktop files")
        else:
            print(f"  ⚠️  rsync failed: {result.stderr.strip()}")


def setup_launch_agents(dotfiles_dir, hostname, home):
    """Setup macOS launch agents"""
    machine_dir = dotfiles_dir / hostname
    launchagents_source_dir = machine_dir / "launchagents"
    launchagents_target_dir = home / "Library" / "LaunchAgents"

    if launchagents_source_dir.exists():
        print("\n🚀 Step 8: Setting up macOS launch agents...")
        launchagents_target_dir.mkdir(parents=True, exist_ok=True)

        # Find all plist files
        plist_files = list(launchagents_source_dir.glob("*.plist"))

        for plist_file in plist_files:
            symlink_target = launchagents_target_dir / plist_file.name

            # Check if already loaded and needs unloading
            if symlink_target.exists() or symlink_target.is_symlink():
                subprocess.run(["launchctl", "unload", str(symlink_target)],
                             stderr=subprocess.DEVNULL, check=False)

            # Create/update symlink
            create_symlink(plist_file, symlink_target, "launch agent")

            # Load the launch agent
            result = subprocess.run(["launchctl", "load", str(symlink_target)],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"  ✅ Loaded {plist_file.name}")
            else:
                print(f"  ⚠️  Failed to load {plist_file.name}: {result.stderr.strip()}")
