#!/usr/bin/env python3

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# === CONFIGURATION === #

LOG_FILE = Path("/tmp/vivaldi_direct.log")
VIVALDI_BIN = "/usr/bin/vivaldi"

# Define profiles and how to launch them
PROFILES = {
    "rash": {
        "profile_directory": "rash",
        "app_url": None,
    },
    "jobhunt": {
        "profile_directory": "jobhunt",
        "app_url": None,
    },
    "chatgpt": {
        "profile_directory": "app_profile",
        "app_url": "https://chat.openai.com",
    },
    "perplexity": {
        "profile_directory": "app_profile",
        "app_url": "https://perplexity.ai",
    },
    "youtube": {
        "profile_directory": "app_profile",
        "app_url": "https://youtube.com",
    },
    "svtplay": {
        "profile_directory": "app_profile",
        "app_url": "https://svtplay.se",
    },
    "max": {
        "profile_directory": "app_profile",
        "app_url": "https://max.com",
    },
    "overseerr": {
        "profile_directory": "app_profile",
        "app_url": "https://watchlist.rashlab.net",
    },
    "github": {
        "profile_directory": "app_profile",
        "app_url": "https://github.com",
    },
    "claude": {
        "profile_directory": "app_profile",
        "app_url": "https://claude.ai",
    },
    "google_calendar": {
        "profile_directory": "app_profile",
        "app_url": "https://calendar.google.com",
    },
}

BASE_ARGS = [
    "--new-window",
    "--new-instance",
    "--ozone-platform=wayland",
    "--enable-features=UseOzonePlatform",
]

# === END CONFIGURATION === #


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a") as f:
        f.write(f"{timestamp}: {message}\n")


def build_command(profile_info: dict) -> list:
    cmd = [VIVALDI_BIN] + BASE_ARGS
    cmd.append(f"--profile-directory={profile_info['profile_directory']}")
    if profile_info.get("app_url"):
        cmd.append(f"--app={profile_info['app_url']}")
    return cmd


def main():
    # Log execution
    log(f"vivaldi_launch called with args: {' '.join(sys.argv[1:])}")

    # Parse arguments
    profile = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--profile" and (i + 1) < len(args):
            profile = args[i + 1]
            i += 2
        else:
            i += 1

    if not profile:
        log("Error: --profile is required")
        sys.exit(1)

    if profile not in PROFILES:
        log(f"Error: Unknown profile {profile}")
        sys.exit(1)

    cmd = build_command(PROFILES[profile])

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f"vivaldi_launch launched Vivaldi with profile {profile}")
    except Exception as e:
        log(f"Error launching Vivaldi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
