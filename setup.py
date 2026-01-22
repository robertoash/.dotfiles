#!/usr/bin/env python3
# /// script
# dependencies = ["pyyaml"]
# ///

import socket
import sys
from pathlib import Path

# Add setup to path for imports
sys.path.insert(0, str(Path(__file__).parent / "setup"))

# Import setup modules
from beads_setup import setup_beads_integration
from claude_setup import setup_claude_config
from config_symlinks import symlink_configs
from crontab_setup import setup_crontab
from desktop_setup import setup_desktop_files, setup_launch_agents
from env_distribution import distribute_env_vars
from hosts_setup import setup_hosts
from machines import get_machine_config
from merge_setup import merge_common_directories
from ssh_setup import setup_ssh
from sudoers_setup import setup_sudoers
from systemd_setup import reload_systemd_daemon
from zen_app_windowrules import generate_zen_app_windowrules

# Get hostname and paths
hostname = socket.gethostname()
home = Path.home()
dotfiles_dir = Path(__file__).parent
machine_config = get_machine_config(hostname)

print(f"🚀 Setting up dotfiles for {hostname}...")

# Step 1: Merge common directories into machine-specific directories
merge_common_directories(dotfiles_dir, hostname)

# Step 2-3: Symlink configs to ~/.config and handle special cases
symlink_warnings = symlink_configs(dotfiles_dir, hostname, home, machine_config)

# Step 5: Setup SSH config and authorized_keys
setup_ssh(dotfiles_dir, hostname, home)

# Step 6: Setup /etc/hosts entries (Linux only)
if machine_config["is_linux"]:
    setup_hosts(dotfiles_dir)

# Step 6.1: Setup sudoers.d configuration (Linux only)
if machine_config["is_linux"]:
    setup_sudoers(dotfiles_dir)

# Step 6.5: Setup Claude Code configuration
setup_claude_config(dotfiles_dir, hostname)

# Step 6.5.1: Setup beads integration
setup_beads_integration(dotfiles_dir)

# Step 6.6: Distribute environment variables
distribute_env_vars(dotfiles_dir, hostname, verbose=True)

# Step 6.7: Generate zen app window rules (Linux only)
if machine_config["is_linux"]:
    generate_zen_app_windowrules(dotfiles_dir, hostname, verbose=True)

# Step 7: Rsync desktop files (Linux only)
if machine_config["is_linux"]:
    setup_desktop_files(dotfiles_dir, hostname, home)

# Step 8: Setup launch agents (macOS only)
if machine_config["is_macos"]:
    setup_launch_agents(dotfiles_dir, hostname, home)

# Step 9: Reload systemd daemon (Linux only)
if machine_config["is_linux"]:
    reload_systemd_daemon(dotfiles_dir, hostname)

# Step 10: Setup backup crontab (Linux only)
if machine_config["is_linux"]:
    setup_crontab(dotfiles_dir, hostname)

# Print warnings about existing valid symlinks if any
if symlink_warnings:
    print("\n⚠️  Warnings:")
    for warning in symlink_warnings:
        print(warning)

print(f"\n🎉 Dotfiles setup complete for {hostname}!")
