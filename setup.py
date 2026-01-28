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
from dictation_setup import setup_dictation
from env_distribution import distribute_env_vars
from hosts_setup import setup_hosts
from machines import get_machine_config
from merge_setup import merge_common_directories
from pacman_setup import setup_pacman
from pam_setup import setup_pam
from security_setup import setup_security
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

# Step 1.5: Merge linuxcommon into Linux machines (linuxmini, oldmbp)
if machine_config["is_linux"] and (dotfiles_dir / "linuxcommon").exists():
    print("\n🐧 Merging linuxcommon directories into Linux machine...")
    from merge_setup import merge_common_directories as merge_linux_common
    # Use same merge function but with linuxcommon as source
    linuxcommon_config = dotfiles_dir / "linuxcommon" / "config"
    machine_config_dir = dotfiles_dir / hostname / "config"
    if linuxcommon_config.exists() and machine_config_dir.exists():
        from symlinks import merge_common_into_machine
        from merge_setup import count_files_to_process, update_gitignore

        total = count_files_to_process(linuxcommon_config, machine_config_dir)
        progress_info = {"current": 0, "total": total, "name": "linuxcommon/config"}
        print(f"🐧 Merging linuxcommon/config... (0/{total} processed)", end='', flush=True)

        all_symlink_paths = merge_common_into_machine(
            linuxcommon_config, machine_config_dir, machine_config_dir, dotfiles_dir, progress_info=progress_info
        )
        print()

        if all_symlink_paths:
            update_gitignore(machine_config_dir, all_symlink_paths, dotfiles_dir)

    # Also merge linuxcommon/systemd into machine's systemd
    linuxcommon_systemd = dotfiles_dir / "linuxcommon" / "systemd" / "user"
    machine_systemd_dir = dotfiles_dir / hostname / "systemd" / "user"
    if linuxcommon_systemd.exists() and machine_systemd_dir.exists():
        total = count_files_to_process(linuxcommon_systemd, machine_systemd_dir)
        progress_info = {"current": 0, "total": total, "name": "linuxcommon/systemd"}
        print(f"🐧 Merging linuxcommon/systemd... (0/{total} processed)", end='', flush=True)

        all_symlink_paths = merge_common_into_machine(
            linuxcommon_systemd, machine_systemd_dir, machine_systemd_dir, dotfiles_dir, progress_info=progress_info
        )
        print()

        if all_symlink_paths:
            update_gitignore(machine_systemd_dir, all_symlink_paths, dotfiles_dir)

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

# Step 10: Setup backup crontab (Linux only)
if machine_config["is_linux"]:
    setup_crontab(dotfiles_dir, hostname)

# Print warnings about existing valid symlinks if any
if symlink_warnings:
    print("\n⚠️  Warnings:")
    for warning in symlink_warnings:
        print(warning)

print(f"\n🎉 Dotfiles setup complete for {hostname}!")
