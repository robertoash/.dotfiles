#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///

import os
import socket
import subprocess
import sys
from pathlib import Path

# Add setup to path for imports
sys.path.insert(0, str(Path(__file__).parent / "setup"))
from claude_setup import setup_claude_config
from env_distribution import distribute_env_vars
from machines import get_machine_config

# Get hostname and paths
hostname = socket.gethostname()
home = Path.home()
dotfiles_dir = Path(__file__).parent
machine_config = get_machine_config(hostname)

print(f"🚀 Setting up dotfiles for {hostname}...")

def create_symlink(source, target, description=""):
    """Create symlink, removing existing file/link if needed"""
    target = Path(target)
    source = Path(source)

    if not source.exists():
        print(f"⚠️  Source does not exist: {source}")
        return

    # Create parent directory if needed
    target.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing target if it exists
    if target.exists() or target.is_symlink():
        if target.is_symlink():
            target.unlink()
        else:
            if target.is_dir():
                subprocess.run(["rm", "-rf", str(target)], check=True)
            else:
                target.unlink()

    # Create symlink
    target.symlink_to(source.resolve())
    desc = f" ({description})" if description else ""
    print(f"✅ {target} -> {source}{desc}")

def merge_common_into_machine(common_dir, machine_dir, config_root, level=0, symlink_paths=None, progress_info=None):
    """
    Populate machine_dir with symlinks to files from common_dir.
    Only creates symlinks for items that don't already exist in machine_dir.
    Recursively merges subdirectories.
    Collects all symlink paths relative to config_root for .gitignore.
    """
    common_dir = Path(common_dir)
    machine_dir = Path(machine_dir)
    config_root = Path(config_root)

    if not common_dir.exists():
        return symlink_paths

    # Create machine_dir if it doesn't exist
    machine_dir.mkdir(parents=True, exist_ok=True)

    # Clean up broken symlinks that were created by setup.py
    # (i.e., symlinks pointing to locations within dotfiles directory)
    if machine_dir.exists():
        for item in machine_dir.iterdir():
            if item.is_symlink() and not item.exists():
                # Broken symlink - check if it points within dotfiles
                try:
                    target = item.resolve(strict=False)
                    if str(target).startswith(str(dotfiles_dir)):
                        # This was created by setup.py, safe to remove
                        item.unlink()
                        if level == 0:
                            print(f"🗑️  Removed broken symlink: {item.name}")
                except (OSError, RuntimeError):
                    pass

    if symlink_paths is None:
        symlink_paths = []

    if progress_info is None:
        progress_info = {"current": 0, "total": 0, "name": ""}

    indent = "  " * level

    # For each item in common_dir
    items = list(common_dir.iterdir())
    for common_app_item in items:
        machine_app_item = machine_dir / common_app_item.name

        # Skip .gitignore files - they should be machine-specific
        if common_app_item.name == '.gitignore':
            continue

        # Update progress counter
        if level >= 0:
            progress_info["current"] += 1
            if progress_info["name"]:
                print(f"\r🔀 Merging {progress_info['name']}... ({progress_info['current']}/{progress_info['total']} processed)", end='', flush=True)

        # If item doesn't exist in machine_dir, create symlink
        if not machine_app_item.exists() and not machine_app_item.is_symlink():
            machine_app_item.symlink_to(common_app_item.resolve())
            if level == 0:
                print(f"\n{indent}📎 {common_app_item.name} -> common")
            # Add relative path from config root
            # Symlinks are always tracked as files (even if they point to directories)
            symlink_paths.append(str(machine_app_item.relative_to(config_root)))
        elif machine_app_item.is_symlink():
            # Symlink already exists - add to gitignore
            if machine_app_item.resolve() == common_app_item.resolve():
                # Symlinks are always tracked as files (even if they point to directories)
                symlink_paths.append(str(machine_app_item.relative_to(config_root)))
            # Don't recurse into symlinked directories
        elif common_app_item.is_dir() and machine_app_item.is_dir() and not machine_app_item.is_symlink():
            # Both are directories and machine_app_item is not a symlink, merge recursively
            merge_common_into_machine(common_app_item, machine_app_item, config_root, level + 1, symlink_paths, progress_info)

    return symlink_paths

# Create ~/.config directory
config_dir = home / ".config"
config_dir.mkdir(exist_ok=True)

# Step 1: Merge common directories (config, secrets) into machine-specific directories
print("\n🔀 Step 1: Merging common directories into machine-specific directories...")

# Directories to merge: config and secrets
merge_dirs = ["config", "secrets"]

for dir_name in merge_dirs:
    common_dir = dotfiles_dir / "common" / dir_name
    machine_dir = dotfiles_dir / hostname / dir_name

    if not common_dir.exists() or not machine_dir.exists():
        continue

    # Count total items for progress
    def count_files_to_process(common_path, machine_path):
        count = 0
        try:
            for common_item in common_path.iterdir():
                count += 1
                machine_item = machine_path / common_item.name
                if common_item.is_dir() and machine_item.exists() and machine_item.is_dir() and not machine_item.is_symlink():
                    count += count_files_to_process(common_item, machine_item)
        except (OSError, PermissionError):
            pass
        return count

    total = count_files_to_process(common_dir, machine_dir)
    progress_info = {"current": 0, "total": total, "name": dir_name}
    icon = "🔐" if dir_name == "secrets" else "📦"
    print(f"{icon} Merging {dir_name}... (0/{total} processed)", end='', flush=True)

    all_symlink_paths = merge_common_into_machine(common_dir, machine_dir, machine_dir, progress_info=progress_info)
    print()

    # Create/update .gitignore
    if all_symlink_paths:
        gitignore_path = machine_dir / ".gitignore"

        from collections import defaultdict
        dir_files = defaultdict(lambda: {"symlinks": set(), "all_files": set()})

        for symlink_path in all_symlink_paths:
            path = Path(symlink_path)
            parent = str(path.parent) if path.parent != Path('.') else ""
            dir_files[parent]["symlinks"].add(symlink_path)
            actual_dir = machine_dir / path.parent
            if actual_dir.exists() and actual_dir.is_dir() and not actual_dir.is_symlink():
                for item in actual_dir.iterdir():
                    rel_path = str(item.relative_to(machine_dir))
                    dir_files[parent]["all_files"].add(rel_path)

        gitignore_entries = []
        for parent_dir, files in sorted(dir_files.items()):
            symlinks = files["symlinks"]
            all_files = files["all_files"]
            if symlinks == all_files and len(all_files) > 0:
                if parent_dir:
                    gitignore_entries.append(f"{parent_dir}/")
            else:
                gitignore_entries.extend(sorted(symlinks))

        gitignore_entries = sorted(set(gitignore_entries))

        # Preserve existing content
        existing_content = ""
        marker_start = "# === AUTO-GENERATED SYMLINKS (do not edit) ===\n"
        marker_end = "# === END AUTO-GENERATED SYMLINKS ===\n"

        if gitignore_path.exists():
            existing = gitignore_path.read_text()
            if marker_start in existing:
                before = existing.split(marker_start)[0]
                if marker_end in existing:
                    after = existing.split(marker_end)[1]
                    existing_content = before + after
                else:
                    existing_content = before
            else:
                existing_content = existing

        gitignore_content = existing_content.rstrip() + "\n\n" if existing_content.strip() else ""
        gitignore_content += marker_start
        gitignore_content += "\n".join(gitignore_entries) + "\n"
        gitignore_content += marker_end

        gitignore_path.write_text(gitignore_content)
        before_count = len(all_symlink_paths)
        after_count = len(gitignore_entries)
        print(f"📝 Updated {gitignore_path.relative_to(dotfiles_dir)} ({after_count} entries, optimized from {before_count} symlinks)")

machine_config_dir = dotfiles_dir / hostname / "config"
common_config_dir = dotfiles_dir / "common" / "config"

# Step 2: Symlink all configs to ~/.config
print("\n🔗 Step 2: Symlinking configs to ~/.config...")

# Track warnings about existing valid symlinks
symlink_warnings = []

# Symlink machine-specific configs (which now contain merged common + machine files)
if machine_config_dir.exists():
    for item in machine_config_dir.iterdir():
        if item.name == ".gitignore":
            continue  # Skip .gitignore - handled in Step 3 from machine directory
        if item.is_dir() or item.is_file():
            target = config_dir / item.name
            create_symlink(item, target, f"{hostname}")

# Symlink common configs that don't have machine-specific versions
if common_config_dir.exists():
    for item in common_config_dir.iterdir():
        target = config_dir / item.name
        # Check if machine-specific version exists
        machine_version = machine_config_dir / item.name if machine_config_dir.exists() else None

        # Skip if machine-specific version exists (it takes precedence)
        if machine_version and machine_version.exists():
            continue

        # Only symlink if not already linked from machine-specific
        if target.is_symlink() and not target.exists():
            # Broken symlink - replace it
            create_symlink(item, target, "common")
        elif target.is_symlink() and target.exists():
            # Check if pointing to machine-specific version (which takes precedence)
            if machine_version and machine_version.exists() and target.resolve() == machine_version.resolve():
                # Correctly pointing to machine version, no warning needed
                pass
            elif target.resolve() != item.resolve():
                # Valid symlink pointing elsewhere - warn but don't replace
                symlink_warnings.append(f"  ⚠️  {target} -> {target.resolve()} (not replaced)")
        elif not target.exists():
            # Doesn't exist - create it
            create_symlink(item, target, "common")

# Step 3: Symlink machine directories directly (not in config/)
machine_dir = dotfiles_dir / hostname
if machine_dir.exists():
    for item in machine_dir.iterdir():
        if item.name == "config":
            continue  # Already handled above
        if item.is_dir() or item.is_file():
            target = config_dir / item.name
            # Only create if doesn't exist or is a broken symlink
            if target.is_symlink() and not target.exists():
                # Broken symlink - replace it
                create_symlink(item, target, f"{hostname} direct")
            elif target.is_symlink() and target.exists():
                # Check if already pointing to this machine's version
                if target.resolve() == item.resolve():
                    # Already correctly linked, no warning needed
                    pass
                else:
                    # Valid symlink pointing elsewhere - warn but don't replace
                    symlink_warnings.append(f"  ⚠️  {target} -> {target.resolve()} (not replaced)")
            elif not target.exists():
                # Doesn't exist - create it
                create_symlink(item, target, f"{hostname} direct")

# 4. Special cases by hostname

# Home directory dotfiles - automatically symlink everything in home/
home_dir = machine_dir / "home"
if home_dir.exists():
    for item in home_dir.iterdir():
        target = home / item.name
        create_symlink(item, target, "home")

# Secrets directory - symlink merged secrets to ~/secrets
machine_secrets_dir = machine_dir / "secrets"
if machine_secrets_dir.exists():
    secrets_target = home / "secrets"
    create_symlink(machine_secrets_dir, secrets_target, "secrets")

# Machine-specific scripts - symlink if they exist
scripts_dir = machine_dir / "scripts"
if scripts_dir.exists():
    create_symlink(scripts_dir, config_dir / "scripts", "scripts")

# Machine-specific local/bin directory - symlink individual files
local_bin_dir = machine_dir / "local" / "bin"
if local_bin_dir.exists():
    local_bin_target = home / ".local" / "bin"
    local_bin_target.mkdir(parents=True, exist_ok=True)
    for script in local_bin_dir.iterdir():
        if script.is_file():
            target = local_bin_target / script.name
            create_symlink(script, target, f"local/bin/{script.name}")

# Step 5: Setup SSH config and authorized_keys
print("\n🔐 Step 5: Setting up SSH config and authorized_keys...")
ssh_dir = home / ".ssh"
ssh_dir.mkdir(mode=0o700, exist_ok=True)

# Symlink SSH config from dotfiles
ssh_config_source = dotfiles_dir / "common" / "ssh" / "config"
ssh_config_target = ssh_dir / "config"

if ssh_config_source.exists():
    # Ensure source file has correct permissions (600)
    subprocess.run(["chmod", "600", str(ssh_config_source)], check=True)
    create_symlink(ssh_config_source, ssh_config_target, "SSH config")
else:
    print(f"⚠️  SSH config source not found: {ssh_config_source}")

# Symlink authorized_keys from dotfiles
authorized_keys_source = dotfiles_dir / "common" / "ssh" / "authorized_keys"
authorized_keys_target = ssh_dir / "authorized_keys"

if authorized_keys_source.exists():
    # Ensure source file has correct permissions (600)
    subprocess.run(["chmod", "600", str(authorized_keys_source)], check=True)
    create_symlink(authorized_keys_source, authorized_keys_target, "SSH authorized_keys")
else:
    print(f"⚠️  SSH authorized_keys source not found: {authorized_keys_source}")

# Step 6: Setup /etc/hosts entries
print("\n🌐 Step 6: Setting up /etc/hosts entries...")
hosts_file = dotfiles_dir / "system" / "hosts"

if hosts_file.exists():
    # Read the hosts entries
    hosts_content = hosts_file.read_text()
    hosts_entries = []

    for line in hosts_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            hosts_entries.append(line)

    if hosts_entries:
        # Check if entries already exist in /etc/hosts
        try:
            etc_hosts = Path("/etc/hosts").read_text()
            marker = "# === DOTFILES MANAGED HOSTS ==="

            if marker not in etc_hosts:
                print(f"  ℹ️  Found {len(hosts_entries)} host entries to add")
                print("  🔒 Adding entries to /etc/hosts (requires sudo)...")

                # Build the content to append
                hosts_content_to_add = f"\n{marker}\n"
                for entry in hosts_entries:
                    hosts_content_to_add += f"{entry}\n"
                hosts_content_to_add += "# === END DOTFILES MANAGED HOSTS ===\n"

                # Use sudo tee to append to /etc/hosts
                result = subprocess.run(
                    ["sudo", "tee", "-a", "/etc/hosts"],
                    input=hosts_content_to_add,
                    text=True,
                    capture_output=True
                )

                if result.returncode == 0:
                    print(f"  ✅ Added {len(hosts_entries)} host entries to /etc/hosts")
                else:
                    print(f"  ⚠️  Failed to add hosts: {result.stderr.strip()}")
            else:
                print("  ✅ /etc/hosts entries already present")
        except PermissionError:
            print("  ⚠️  Cannot read /etc/hosts (permission denied)")

# Step 6.5: Setup Claude Code configuration
setup_claude_config(dotfiles_dir, hostname)

# Step 6.6: Distribute environment variables from system/env_vars.yaml
distribute_env_vars(dotfiles_dir, hostname, verbose=True)

# Step 7: Rsync desktop files (Linux only)
if machine_config["is_linux"]:
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

# Step 8: Setup launch agents (macOS only)
if machine_config["is_macos"]:
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

# Step 9: Reload systemd daemon (Linux only)
if machine_config["is_linux"]:
    systemd_user_dir = machine_dir / "systemd" / "user"

    if systemd_user_dir.exists():
        print("\n⚙️  Step 9: Reloading systemd user daemon...")
        # Reload systemd daemon
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
        print("  🔄 Systemd user daemon reloaded")

# Step 10: Setup backup crontab (Linux only)
if machine_config["is_linux"]:
    backup_crontab_file = machine_dir / "scripts" / "backup" / "crontab" / "bkup_crontab_entries.txt"

    if backup_crontab_file.exists():
        print("\n📅 Step 10: Setting up backup crontab...")

        # Check if cronie is installed
        cronie_check = subprocess.run(["which", "crontab"], capture_output=True)

        if cronie_check.returncode == 0:
            # Read crontab entries file
            crontab_content = backup_crontab_file.read_text()

            # Extract user crontab entries (before "#### Sudo Crontab")
            user_entries = []
            sudo_entries = []
            in_sudo_section = False

            for line in crontab_content.split('\n'):
                line = line.strip()
                if line.startswith("#### Sudo Crontab"):
                    in_sudo_section = True
                    continue
                if line and not line.startswith('#'):
                    if in_sudo_section:
                        # Remove 'sudo' from the command for sudo crontab
                        sudo_entries.append(line.replace('sudo ', '', 1))
                    else:
                        user_entries.append(line)

            if user_entries:
                # Get existing crontab
                existing_result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
                existing_crontab = existing_result.stdout if existing_result.returncode == 0 else ""

                # Check if backup entries already exist
                marker = "# === BACKUP CRONTAB ENTRIES ==="
                if marker not in existing_crontab:
                    # Append new entries
                    new_crontab = existing_crontab.rstrip()
                    if new_crontab:
                        new_crontab += "\n\n"
                    new_crontab += f"{marker}\n"
                    new_crontab += "\n".join(user_entries) + "\n"

                    # Load new crontab
                    load_result = subprocess.run(
                        ["crontab", "-"],
                        input=new_crontab,
                        text=True,
                        capture_output=True
                    )

                    if load_result.returncode == 0:
                        print(f"  ✅ Loaded {len(user_entries)} user crontab entries")
                    else:
                        print(f"  ⚠️  Failed to load crontab: {load_result.stderr.strip()}")
                else:
                    print("  ℹ️  Backup crontab entries already loaded")

            # Setup sudo crontab automatically
            if sudo_entries:
                print("\n  🔒 Setting up root crontab (requires sudo)...")

                # Get existing root crontab
                existing_result = subprocess.run(
                    ["sudo", "crontab", "-l"],
                    capture_output=True,
                    text=True
                )
                existing_root_crontab = existing_result.stdout if existing_result.returncode == 0 else ""

                # Check if backup entries already exist
                root_marker = "# === BACKUP CRONTAB ENTRIES ==="
                if root_marker not in existing_root_crontab:
                    # Append new entries
                    new_root_crontab = existing_root_crontab.rstrip()
                    if new_root_crontab:
                        new_root_crontab += "\n\n"
                    new_root_crontab += f"{root_marker}\n"
                    new_root_crontab += "\n".join(sudo_entries) + "\n"

                    # Load new root crontab
                    load_result = subprocess.run(
                        ["sudo", "crontab", "-"],
                        input=new_root_crontab,
                        text=True,
                        capture_output=True
                    )

                    if load_result.returncode == 0:
                        print(f"  ✅ Loaded {len(sudo_entries)} root crontab entries")
                    else:
                        print(f"  ⚠️  Failed to load root crontab: {load_result.stderr.strip()}")
                else:
                    print("  ℹ️  Root backup crontab entries already loaded")
        else:
            print("  ⚠️  crontab not found - install cronie package")

# Print warnings about existing valid symlinks if any
if symlink_warnings:
    print("\n⚠️  Warnings:")
    for warning in symlink_warnings:
        print(warning)

print(f"\n🎉 Dotfiles setup complete for {hostname}!")