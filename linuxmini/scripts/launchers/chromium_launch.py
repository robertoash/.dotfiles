#!/usr/bin/env python3
import subprocess
import sys
import json
from datetime import datetime
from pathlib import Path

# === CONFIGURATION === #
LOG_FILE = Path("/tmp/brave_browser_direct.log")
CHROMIUM_BIN = "/usr/bin/brave"
CONFIG_FILE = Path.home() / ".config/hypr/script_configs/zen_apps.json"


def load_profiles():
    """Load profiles from JSON configuration file and browser profiles from config.py."""
    try:
        # Load zen apps config
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        # Flatten the structure while preserving type information
        profiles = {}
        for profile_type, type_profiles in config.items():
            for name, profile_data in type_profiles.items():
                profiles[name] = {**profile_data, "type": profile_type}

        # Add browser profile launchers from hypr_window_ops config
        try:
            import sys

            config_dir = Path.home() / ".config/scripts/hyprland/hypr_window_ops"
            sys.path.insert(0, str(config_dir))

            from hypr_window_ops import config

            # Add browser profiles with "url" type
            for name, profile_data in config.BROWSER_PROFILES.items():
                profiles[name] = {**profile_data, "type": "url"}
        except Exception as e:
            log(f"Warning: Could not load browser profiles from config.py: {e}")

        return profiles
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log(f"Error loading config file {CONFIG_FILE}: {e}")
        sys.exit(1)


# Brave command-line arguments
BASE_ARGS = [
    "--new-window",
    "--new-instance",
    "--disable-features=WaylandWpColorManagerV1,TranslateUI",
    # Performance optimizations
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-sync",
    "--disable-translate",
    # Minimal UI in app mode
    "--disable-popup-blocking",
]

# === END CONFIGURATION === #


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a") as f:
        f.write(f"{timestamp}: {message}\n")


def build_command(profile_info: dict, profile_name: str) -> list:
    cmd = [CHROMIUM_BIN] + BASE_ARGS
    cmd.append(f"--profile-directory={profile_info['profile_directory']}")

    # Set different class names for extensions
    if profile_info.get("type") == "extension":
        cmd.append(f"--app-name={profile_name.capitalize()}-Ext")

    if profile_info.get("app_url"):
        cmd.append(f"--app={profile_info['app_url']}")
    return cmd


def main():
    # Log execution
    log(f"chromium_launch called with args: {' '.join(sys.argv[1:])}")

    # Load profiles from JSON config
    profiles = load_profiles()

    # Parse arguments
    profile = None
    url = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--profile" and (i + 1) < len(args):
            profile = args[i + 1]
            i += 2
        elif args[i].startswith("http"):
            # Assume any argument starting with http is a URL
            url = args[i]
            i += 1
        else:
            i += 1

    if not profile:
        log("Error: --profile is required")
        sys.exit(1)

    if profile not in profiles:
        log(f"Error: Unknown profile {profile}")
        sys.exit(1)

    cmd = build_command(profiles[profile], profile)

    # Add URL if provided
    if url:
        cmd.append(url)
        log(f"Adding URL to command: {url}")

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(
            f"chromium_launch launched Brave with profile {profile}"
            + (f" and URL {url}" if url else "")
        )
    except Exception as e:
        log(f"Error launching Brave: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
