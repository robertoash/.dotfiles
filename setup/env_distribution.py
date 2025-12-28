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


def expand_home(val: str, home_dir: str) -> str:
    """Expand $HOME and ~ in a value."""
    val = str(val).replace("$HOME", home_dir)
    if val.startswith("~/"):
        val = val.replace("~/", f"{home_dir}/", 1)
    elif val == "~":
        val = home_dir
    return val


def generate_systemd_env_file(config: Dict[str, Any], machine: str) -> str:
    """
    Generate systemd environment.d file from global + machine-specific vars.
    PATH is merged: machine-specific paths are prepended to global paths.
    Returns the file content as a string.
    """
    lines = [
        "# AUTO-GENERATED FROM ~/.dotfiles/system/env_vars.yaml",
        "# DO NOT EDIT MANUALLY - Run setup.py to regenerate",
        "# Edit ~/.dotfiles/system/env_vars.yaml instead",
        "",
    ]

    home_dir = str(Path.home())
    machine_vars = {}
    if "machines" in config and machine in config["machines"] and config["machines"][machine]:
        machine_vars = config["machines"][machine]

    # Build merged PATH: machine_paths + system_paths + global_custom_paths
    path_components = []

    # 1. Machine-specific paths (prepended)
    if "PATH" in machine_vars:
        machine_path = expand_home(machine_vars["PATH"], home_dir)
        path_components.append(machine_path)

    # 2. Standard system paths
    path_components.append("/usr/local/bin:/usr/bin:/bin")

    # 3. Global custom paths (from env_vars.yaml global.PATH, stripping $PATH:)
    if "global" in config and "PATH" in config["global"]:
        global_path = expand_home(config["global"]["PATH"], home_dir)
        custom_paths = global_path.replace("$PATH:", "").strip()
        if custom_paths:
            path_components.append(custom_paths)

    # Add global variables
    if "global" in config:
        lines.append("# Global variables")
        for key, val in config["global"].items():
            # Skip GTK_THEME - it goes in theme.conf
            if key == "GTK_THEME":
                continue
            # Skip PATH - handled separately with merging
            if key == "PATH":
                continue
            val = expand_home(val, home_dir)
            lines.append(f"{key}={val}")
        # Add merged PATH
        lines.append(f"PATH={':'.join(path_components)}")
        lines.append("")

    # Add machine-specific overrides (excluding PATH, already merged)
    non_path_machine_vars = {k: v for k, v in machine_vars.items() if k != "PATH"}
    if non_path_machine_vars:
        lines.append(f"# {machine}-specific variables")
        for key, val in non_path_machine_vars.items():
            val = expand_home(val, home_dir)
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

    home_dir = str(Path.home())

    # Add PATH from global if it exists
    if "global" in config and "PATH" in config["global"]:
        path_value = config["global"]["PATH"]
        # Keep $PATH for appending, just expand $HOME
        path_value = path_value.replace("$HOME", home_dir)
        lines.append(f"env = PATH,{path_value}")
        lines.append("")

    # Add Hyprland-specific variables
    if "hyprland_only" in config:
        lines.append("# Hyprland/Wayland-specific variables")
        lines.append("# NOTE: DISPLAY and WAYLAND_DISPLAY are set by Hyprland automatically - don't override")
        for key, val in config["hyprland_only"].items():
            # Expand $HOME if present
            val = str(val).replace("$HOME", home_dir)
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
