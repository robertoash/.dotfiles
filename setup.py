#!/usr/bin/env python3

import os
import socket
import subprocess
from pathlib import Path

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

def merge_common_into_machine(common_dir, machine_dir, config_root, level=0, symlink_paths=None):
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

    indent = "  " * level

    # For each item in common_dir
    for common_item in common_dir.iterdir():
        machine_item = machine_dir / common_item.name

        # If item doesn't exist in machine_dir, create symlink
        if not machine_item.exists() and not machine_item.is_symlink():
            machine_item.symlink_to(common_item.resolve())
            if level == 0:
                print(f"{indent}📎 {common_item.name} -> common")
            # Add relative path from config root
            symlink_paths.append(str(machine_item.relative_to(config_root)))
        elif machine_item.is_symlink() and machine_item.resolve() == common_item.resolve():
            # Symlink already exists pointing to common - add to gitignore
            symlink_paths.append(str(machine_item.relative_to(config_root)))
        elif common_item.is_dir() and machine_item.is_dir() and not machine_item.is_symlink():
            # Both are directories and machine_item is not a symlink, merge recursively
            merge_common_into_machine(common_item, machine_item, config_root, level + 1, symlink_paths)

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
    for common_item in common_config_dir.iterdir():
        machine_item = machine_config_dir / common_item.name

        # If both exist and both are directories, merge recursively
        if machine_item.exists() and common_item.is_dir() and machine_item.is_dir():
            print(f"🔀 Merging {common_item.name}...")
            symlink_paths = merge_common_into_machine(common_item, machine_item, machine_config_dir)
            if symlink_paths:
                all_symlink_paths.extend(symlink_paths)

    # Create/update .gitignore with all symlink paths
    if all_symlink_paths:
        gitignore_path = machine_config_dir / ".gitignore"

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
        gitignore_content += "\n".join(sorted(all_symlink_paths)) + "\n"
        gitignore_content += marker_end

        gitignore_path.write_text(gitignore_content)
        print(f"📝 Updated {gitignore_path.relative_to(dotfiles_dir)} ({len(all_symlink_paths)} symlinks)")

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

print(f"\n🎉 Dotfiles setup complete for {hostname}!")