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
APP_PROFILES_PATH = HOME / ".config" / "hypr" / "launch_apps.json"
DEFAULT_PROFILE = "personal"

# Delays
WINDOW_DELAY = 0.5
FOCUS_DELAY = 0.5
WINDOW_CREATION_DELAY = 0.5


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
