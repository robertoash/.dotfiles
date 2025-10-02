#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

# Common paths
HOME = Path.home()
CONFIG_DIR = os.environ.get("DOTFILES_DIR", str(HOME / ".config"))
CURRENT_PROJECT_DIR = os.environ.get("CURRENT_PROJECT_DIR", str(HOME / "dev/apps/"))

# App profiles config
APP_PROFILES_PATH = HOME / ".config" / "hypr" / "script_configs" / "launch_apps.json"
DEFAULT_PROFILE = "personal"

# Browser profile launchers (used by rofi_profile_selector.py)
BROWSER_PROFILES = {
    "rash": {
        "profile_directory": "rash",
        "app_url": None
    },
    "work": {
        "profile_directory": "work",
        "app_url": None
    },
    "app": {
        "profile_directory": "app",
        "app_url": None
    },
    "dash": {
        "profile_directory": "dash",
        "app_url": None
    }
}

# Delays
# INITIAL_DELAY: Time to wait before starting to launch any apps.
# Allows the window manager to stabilize after profile switch.
INITIAL_DELAY = 0.5

# FOCUS_DELAY: Time to wait after focusing a workspace.
# Used after switching to workspace 11 or 1 at the end of the launch process.
FOCUS_WS_DELAY = 0.2

# WINDOW_CREATION_DELAY: Time to wait after launching each app.
# Allows the app's window to appear before continuing (prevents race conditions).
WINDOW_CREATION_DELAY = 1

# MAX_WAIT_FOR_WINDOW: Maximum time (in seconds) to wait for a new window to appear after
# launching an app.
# Used by wait_for_window to avoid hanging indefinitely if a window fails to appear.
MAX_WAIT_FOR_WINDOW = 1


# Load APP_PROFILES from external JSON file
def load_app_profiles():
    """Load app profiles from external JSON file."""
    if APP_PROFILES_PATH.exists():
        try:
            with open(APP_PROFILES_PATH, "r") as f:
                data = json.load(f)

            # Validate that the data contains at least basic profile structure
            if not data or not isinstance(data, dict) or len(data) == 0:
                print(
                    f"Error: App profiles file at {APP_PROFILES_PATH} is empty or invalid."
                )
                sys.exit(1)

            return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading app profiles from {APP_PROFILES_PATH}: {e}")
            sys.exit(1)
    else:
        print(f"Error: App profiles file not found at {APP_PROFILES_PATH}")
        sys.exit(1)


# Load the app profiles from external file or use defaults
APP_PROFILES = load_app_profiles()
