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

# Create ~/.config directory
config_dir = home / ".config"
config_dir.mkdir(exist_ok=True)

# 1. Symlink common configs for all machines
common_config_dir = dotfiles_dir / "common" / "config"
if common_config_dir.exists():
    for item in common_config_dir.iterdir():
        if item.is_dir() or item.is_file():
            target = config_dir / item.name
            create_symlink(item, target, "common")

# 2. Symlink machine-specific configs
machine_config_dir = dotfiles_dir / hostname / "config"
if machine_config_dir.exists():
    for item in machine_config_dir.iterdir():
        if item.is_dir() or item.is_file():
            target = config_dir / item.name
            create_symlink(item, target, f"{hostname} specific")

# 3. Symlink machine directories directly (not in config/)
machine_dir = dotfiles_dir / hostname
if machine_dir.exists():
    for item in machine_dir.iterdir():
        if item.name == "config":
            continue  # Already handled above
        if item.is_dir() or item.is_file():
            target = config_dir / item.name
            create_symlink(item, target, f"{hostname} direct")

# 4. Special cases by hostname
if hostname == "workmbp":
    # macOS special locations
    special_locations = {
        # Hammerspoon
        dotfiles_dir / "workmbp" / ".hammerspoon": home / ".hammerspoon",
        
        # Snowflake config (special location)
        dotfiles_dir / "workmbp" / "config" / "snowflake" / "config.toml": home / ".snowflake" / "config.toml",
        
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

# Note about fish config merging for machines with extensions
machine_fish_dir = dotfiles_dir / hostname / "config" / "fish"
if machine_fish_dir.exists():
    print(f"\n⚠️  Note: {hostname} has machine-specific fish configs.")
    print(f"   You may need to handle fish config merging separately.")
    print(f"   Common: ~/.config/fish (from common/config/fish)")
    print(f"   Machine-specific: {machine_fish_dir}")