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
from backup_setup import backup_configs, restore_configs
from beads_setup import setup_beads_integration
from claude_setup import setup_claude_config
from symlink_setup import symlink_configs
from crontab_setup import setup_crontab
from desktop_setup import setup_desktop_files, setup_launch_agents
from dictation_setup import setup_dictation
from env_distribution import distribute_env_vars
from hosts_setup import setup_hosts
from machines import get_machine_config
from merge_setup import (
    merge_common_directories,
    merge_machine_specific,
    prepare_hierarchical_merge,
)
from nftables_setup import setup_nftables
from pacman_setup import setup_pacman
from pam_setup import setup_pam
from security_setup import setup_security
from ssh_setup import setup_ssh
from sudoers_setup import setup_sudoers
from resolved_setup import setup_resolved
from systemd_setup import reload_systemd_daemon
from zen_windowrule_setup import generate_zen_app_windowrules
from nvim_setup import check_nvim_dependencies
from git_setup import apply_git_index_flags

# Get hostname and paths
hostname = socket.gethostname()
home = Path.home()
dotfiles_dir = Path(__file__).parent
machine_config = get_machine_config(hostname)

print(f"🚀 Setting up dotfiles for {hostname}...")

# Step 0: Prepare for hierarchical merge (remove blocking symlinks)
prepare_hierarchical_merge(dotfiles_dir, hostname, machine_config)

# Step 1: Merge common directories into machine-specific directories
merge_common_directories(dotfiles_dir, hostname, machine_config)

# Step 1.5: Merge linuxcommon into Linux machines
if machine_config["is_linux"]:
    from merge_setup import merge_linuxcommon_directories
    merge_linuxcommon_directories(dotfiles_dir, hostname, machine_config)

# Step 1.6: Merge servercommon into server machines
if machine_config.get("is_server"):
    from merge_setup import merge_servercommon_directories
    merge_servercommon_directories(dotfiles_dir, hostname)

# Step 1.7: Merge machine-specific configs with non-standard targets
merge_machine_specific(dotfiles_dir, hostname)

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

# Step 6.2: Setup /etc/security/ configuration (Linux only)
if machine_config["is_linux"]:
    setup_security(dotfiles_dir)

# Step 6.3: Setup PAM configuration (Linux only)
if machine_config["is_linux"]:
    setup_pam(dotfiles_dir)

# Step 6.4: Setup pacman configuration (Arch Linux only)
if machine_config["is_linux"]:
    setup_pacman(dotfiles_dir)

# Step 6.4.1: Setup nftables firewall configuration (Linux only)
if machine_config["is_linux"]:
    setup_nftables(dotfiles_dir, hostname)

# Step 6.5: Setup Claude Code configuration
setup_claude_config(dotfiles_dir, hostname)

# Step 6.5.1: Setup beads integration
setup_beads_integration(dotfiles_dir)

# Step 6.5.2: Setup system-wide voice dictation (Linux with Wayland only)
# This works in ALL applications including Claude Code, browsers, terminals, etc.
# Set skip_install=True and skip_setup=True after initial setup
if machine_config["is_linux"] and hostname == "linuxmini":
    setup_dictation(skip_install=False, skip_setup=False)

# Step 6.6: Distribute environment variables
distribute_env_vars(dotfiles_dir, hostname, verbose=True)

# Step 6.7: Generate zen app window rules (Linux only, Hyprland only)
hypr_config_exists = (dotfiles_dir / hostname / "config" / "hypr" / "script_configs" / "zen_apps.json").exists()
if machine_config["is_linux"] and hypr_config_exists:
    generate_zen_app_windowrules(dotfiles_dir, hostname, verbose=True)

# Step 7: Rsync desktop files (Linux only)
if machine_config["is_linux"]:
    setup_desktop_files(dotfiles_dir, hostname, home)

# Step 8: Setup launch agents (macOS only)
if machine_config["is_macos"]:
    setup_launch_agents(dotfiles_dir, hostname, home)

# Step 9: Setup systemd services and reload daemon (Linux only)
if machine_config["is_linux"]:
    reload_systemd_daemon(dotfiles_dir, hostname, machine_config)

# Step 9.5: Setup systemd-resolved configuration (Linux only)
if machine_config["is_linux"]:
    setup_resolved(dotfiles_dir, hostname, machine_config)

# Step 10: Setup backup crontab (Linux only)
if machine_config["is_linux"]:
    setup_crontab(dotfiles_dir, hostname)

# Step 11: Backup application configs that break symlinks
backup_configs(dotfiles_dir, hostname)

# Step 12: Apply git index flags for files with spurious changes
apply_git_index_flags(dotfiles_dir)

# Print warnings about existing valid symlinks if any
if symlink_warnings:
    print("\n⚠️  Warnings:")
    for warning in symlink_warnings:
        print(warning)

# Check Neovim dependencies
check_nvim_dependencies()

print(f"\n🎉 Dotfiles setup complete for {hostname}!")
