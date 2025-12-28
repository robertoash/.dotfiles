#!/usr/bin/env python3
"""
Environment variable distribution system.
Reads system/env_vars.yaml and generates:
- ~/.config/environment.d/env_vars.conf (systemd user environment)
- {machine}/config/hypr/env.conf (Hyprland config - Linux only)
"""

import socket
from pathlib import Path
from typing import Dict, Any
import yaml


def get_current_machine() -> str:
    """Get current machine hostname"""
    return socket.gethostname()


def load_env_config(dotfiles_dir: Path) -> Dict[str, Any]:
    """Load environment variables configuration from YAML"""
    config_file = dotfiles_dir / "system" / "env_vars.yaml"

    if not config_file.exists():
        raise FileNotFoundError(f"Environment config not found: {config_file}")

    with open(config_file) as f:
        return yaml.safe_load(f)


def generate_systemd_env_file(config: Dict[str, Any], machine: str) -> str:
    """
    Generate systemd environment.d file from global + machine-specific vars.
    Returns the file content as a string.
    """
    lines = [
        "# AUTO-GENERATED FROM ~/.dotfiles/system/env_vars.yaml",
        "# DO NOT EDIT MANUALLY - Run setup.py to regenerate",
        "# Edit ~/.dotfiles/system/env_vars.yaml instead",
        "",
    ]

    # Add global variables
    if "global" in config:
        lines.append("# Global variables")
        for key, val in config["global"].items():
            lines.append(f"{key}={val}")
        lines.append("")

    # Add machine-specific overrides
    if "machines" in config and machine in config["machines"]:
        lines.append(f"# {machine}-specific variables")
        for key, val in config["machines"][machine].items():
            lines.append(f"{key}={val}")
        lines.append("")

    return "\n".join(lines)


def generate_hyprland_env_file(config: Dict[str, Any]) -> str:
    """
    Generate Hyprland env.conf with ONLY Hyprland-specific variables.
    Returns the file content as a string.
    """
    lines = [
        "# AUTO-GENERATED FROM ~/.dotfiles/system/env_vars.yaml",
        "# DO NOT EDIT MANUALLY - Run setup.py to regenerate",
        "# Edit ~/.dotfiles/system/env_vars.yaml instead",
        "",
        "# PATH - needed early for Hyprland to launch applications",
    ]

    # Add PATH from global if it exists
    if "global" in config and "PATH" in config["global"]:
        path_value = config["global"]["PATH"]
        # Remove the $PATH: prefix for Hyprland format
        path_value = path_value.replace("$PATH:", "").replace("$HOME", "/home/rash")
        lines.append(f"env = PATH,{path_value}")
        lines.append("")

    # Add Hyprland-specific variables
    if "hyprland_only" in config:
        lines.append("# Hyprland/Wayland-specific variables")
        lines.append("# NOTE: DISPLAY and WAYLAND_DISPLAY are set by Hyprland automatically - don't override")
        for key, val in config["hyprland_only"].items():
            lines.append(f"env = {key},{val}")
        lines.append("")

    return "\n".join(lines)


def distribute_env_vars(dotfiles_dir: Path, machine: str, verbose: bool = True) -> None:
    """
    Main distribution function.
    Reads env_vars.yaml and generates all necessary config files.
    """
    if verbose:
        print("\n📝 Distributing environment variables from system/env_vars.yaml...")

    # Load configuration
    config = load_env_config(dotfiles_dir)

    # 1. Generate systemd environment.d file
    systemd_dir = Path.home() / ".config" / "environment.d"
    systemd_dir.mkdir(parents=True, exist_ok=True)
    systemd_file = systemd_dir / "env_vars.conf"

    systemd_content = generate_systemd_env_file(config, machine)
    systemd_file.write_text(systemd_content)

    if verbose:
        print(f"  ✅ Generated {systemd_file}")

    # 2. Generate theme.conf (separate file for easier editing)
    theme_file = systemd_dir / "theme.conf"
    if "global" in config and "GTK_THEME" in config["global"]:
        theme_content = f"# Theme configuration\nGTK_THEME={config['global']['GTK_THEME']}\n"
        theme_file.write_text(theme_content)
        if verbose:
            print(f"  ✅ Generated {theme_file}")

    # 3. Generate Hyprland config (Linux only)
    if machine == "linuxmini":
        hypr_file = dotfiles_dir / machine / "config" / "hypr" / "env.conf"
        hypr_content = generate_hyprland_env_file(config)
        hypr_file.write_text(hypr_content)
        if verbose:
            print(f"  ✅ Generated {hypr_file}")

    if verbose:
        print("  ✨ Environment variable distribution complete!")


if __name__ == "__main__":
    # Allow running this script standalone for testing
    dotfiles_dir = Path(__file__).parent.parent
    machine = get_current_machine()
    distribute_env_vars(dotfiles_dir, machine, verbose=True)
    print("  💡 Reload systemd: systemctl --user daemon-reload")
    print("  💡 Or restart your session to apply changes")
