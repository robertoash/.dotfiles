#!/usr/bin/env python3

import os
import socket
import subprocess
import sys
from pathlib import Path

# Add setup to path for imports
sys.path.insert(0, str(Path(__file__).parent / "setup"))
from claude_setup import setup_claude_config

# Get hostname and paths
hostname = socket.gethostname()
home = Path.home()
dotfiles_dir = Path(__file__).parent

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

common_config_dir = dotfiles_dir / "common" / "config"
machine_config_dir = dotfiles_dir / hostname / "config"

# Step 1: Merge common configs into machine-specific directories (in the repo)
print("\n📦 Step 1: Merging common configs into machine-specific directories...")
all_symlink_paths = []
if common_config_dir.exists() and machine_config_dir.exists():
    for common_app_item in common_config_dir.iterdir():
        machine_app_item = machine_config_dir / common_app_item.name

        # If both exist and both are directories (and machine is not a symlink), merge recursively
        if machine_app_item.exists() and common_app_item.is_dir() and machine_app_item.is_dir() and not machine_app_item.is_symlink():
            # Count total items that will actually be processed (mirrors merge logic exactly)
            def count_files_to_process(common_path, machine_path):
                count = 0
                try:
                    for common_item in common_path.iterdir():
                        count += 1  # Count this item
                        machine_item = machine_path / common_item.name

                        # If both are directories and machine is not a symlink, recurse
                        if common_item.is_dir() and machine_item.exists() and machine_item.is_dir() and not machine_item.is_symlink():
                            count += count_files_to_process(common_item, machine_item)
                except (OSError, PermissionError):
                    pass
                return count

            total = count_files_to_process(common_app_item, machine_app_item)
            progress_info = {"current": 0, "total": total, "name": common_app_item.name}
            print(f"🔀 Merging {common_app_item.name}... (0/{total} processed)", end='', flush=True)
            symlink_paths = merge_common_into_machine(common_app_item, machine_app_item, machine_config_dir, progress_info=progress_info)
            print()  # New line after progress complete
            if symlink_paths:
                all_symlink_paths.extend(symlink_paths)

    # Create/update .gitignore with all symlink paths
    if all_symlink_paths:
        gitignore_path = machine_config_dir / ".gitignore"

        # Optimize symlinks: group by parent directory
        # If all files in a directory are symlinks, just ignore the directory
        from collections import defaultdict
        dir_files = defaultdict(lambda: {"symlinks": set(), "all_files": set()})

        for symlink_path in all_symlink_paths:
            path = Path(symlink_path)
            parent = str(path.parent) if path.parent != Path('.') else ""
            dir_files[parent]["symlinks"].add(symlink_path)
            # Check actual filesystem to see all files in this directory
            actual_dir = machine_config_dir / path.parent
            if actual_dir.exists() and actual_dir.is_dir() and not actual_dir.is_symlink():
                for item in actual_dir.iterdir():
                    rel_path = str(item.relative_to(machine_config_dir))
                    dir_files[parent]["all_files"].add(rel_path)

        # Determine what to add to gitignore: directories or individual files
        gitignore_entries = []

        for parent_dir, files in sorted(dir_files.items()):
            symlinks = files["symlinks"]
            all_files = files["all_files"]

            # If all files in this directory are symlinks, just ignore the directory
            if symlinks == all_files and len(all_files) > 0:
                # Add directory pattern
                if parent_dir:
                    gitignore_entries.append(f"{parent_dir}/")
            else:
                # Add individual symlink files
                gitignore_entries.extend(sorted(symlinks))

        # Remove duplicates and sort
        gitignore_entries = sorted(set(gitignore_entries))

        # Preserve existing .gitignore content if it exists
        existing_content = ""
        marker_start = "# === AUTO-GENERATED SYMLINKS (do not edit) ===\n"
        marker_end = "# === END AUTO-GENERATED SYMLINKS ===\n"

        if gitignore_path.exists():
            existing = gitignore_path.read_text()
            # Remove old auto-generated section if it exists
            if marker_start in existing:
                before = existing.split(marker_start)[0]
                if marker_end in existing:
                    after = existing.split(marker_end)[1]
                    existing_content = before + after
                else:
                    existing_content = before
            else:
                existing_content = existing

        # Build new content
        gitignore_content = existing_content.rstrip() + "\n\n" if existing_content.strip() else ""
        gitignore_content += marker_start
        gitignore_content += "\n".join(gitignore_entries) + "\n"
        gitignore_content += marker_end

        gitignore_path.write_text(gitignore_content)
        before_count = len(all_symlink_paths)
        after_count = len(gitignore_entries)
        print(f"📝 Updated {gitignore_path.relative_to(dotfiles_dir)} ({after_count} entries, optimized from {before_count} symlinks)")

# Step 2: Symlink all configs to ~/.config
print("\n🔗 Step 2: Symlinking configs to ~/.config...")

# Symlink machine-specific configs (which now contain merged common + machine files)
if machine_config_dir.exists():
    for item in machine_config_dir.iterdir():
        if item.is_dir() or item.is_file():
            target = config_dir / item.name
            create_symlink(item, target, f"{hostname}")

# Symlink common configs that don't have machine-specific versions
if common_config_dir.exists():
    for item in common_config_dir.iterdir():
        target = config_dir / item.name
        # Only symlink if not already linked from machine-specific
        if not target.exists() and not target.is_symlink():
            create_symlink(item, target, "common")

# Step 3: Symlink machine directories directly (not in config/)
machine_dir = dotfiles_dir / hostname
if machine_dir.exists():
    for item in machine_dir.iterdir():
        if item.name == "config":
            continue  # Already handled above
        if item.is_dir() or item.is_file():
            target = config_dir / item.name
            # Only create if doesn't exist
            if not target.exists() and not target.is_symlink():
                create_symlink(item, target, f"{hostname} direct")

# 4. Special cases by hostname
if hostname == "workmbp":
    # macOS special locations
    special_locations = {
        # Hammerspoon
        dotfiles_dir / "workmbp" / ".hammerspoon": home / ".hammerspoon",
        
        # Snowflake config (special location)
        dotfiles_dir / "workmbp" / "snowflake" / "config.toml": home / ".snowflake" / "config.toml",
        
        # Raycast (in ~/.config but from workmbp root, not workmbp/config)
        dotfiles_dir / "workmbp" / "raycast": config_dir / "raycast",
    }
    
    for source, target in special_locations.items():
        create_symlink(source, target, "macOS special")

elif hostname in ["linuxmini", "oldmbp"]:
    # Linux-specific: symlink scripts from linuxmini
    scripts_dir = dotfiles_dir / "linuxmini" / "scripts"
    if scripts_dir.exists():
        create_symlink(scripts_dir, config_dir / "scripts", "Linux scripts")

# Step 5: Setup SSH authorized_keys
print("\n🔐 Step 5: Setting up SSH authorized_keys...")
ssh_dir = home / ".ssh"
ssh_dir.mkdir(mode=0o700, exist_ok=True)

# Symlink authorized_keys from dotfiles
authorized_keys_source = dotfiles_dir / "common" / "ssh" / "authorized_keys"
authorized_keys_target = ssh_dir / "authorized_keys"

if authorized_keys_source.exists():
    # Ensure source file has correct permissions (600)
    subprocess.run(["chmod", "600", str(authorized_keys_source)], check=True)
    create_symlink(authorized_keys_source, authorized_keys_target, "SSH keys")
else:
    print(f"⚠️  SSH authorized_keys source not found: {authorized_keys_source}")

# Step 6: Setup Claude Code configuration
setup_claude_config(dotfiles_dir)

print(f"\n🎉 Dotfiles setup complete for {hostname}!")