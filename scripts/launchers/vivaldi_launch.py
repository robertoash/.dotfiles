#!/usr/bin/env python3

import os
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
    "ha": {
        "profile_directory": "app_profile",
        "app_url": "https://ha.rashlab.net",
    },
    "app_profile": {
        "profile_directory": "app_profile",
        "app_url": None,
    },
}

BASE_ARGS = [
    "--new-window",
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
    # Set up environment for GUI applications (important for cron)
    if "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"
    if "XDG_RUNTIME_DIR" not in os.environ:
        os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"

    # Log execution and environment
    log(f"vivaldi_launch called with args: {' '.join(sys.argv[1:])}")
    log(f"Environment - DISPLAY: {os.environ.get('DISPLAY', 'NOT SET')}")
    log(
        f"Environment - XDG_RUNTIME_DIR: {os.environ.get('XDG_RUNTIME_DIR', 'NOT SET')}"
    )
    log(
        f"Environment - WAYLAND_DISPLAY: {os.environ.get('WAYLAND_DISPLAY', 'NOT SET')}"
    )

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

    if profile not in PROFILES:
        log(f"Error: Unknown profile {profile}")
        sys.exit(1)

    cmd = build_command(PROFILES[profile])

    # Add URL if provided
    if url:
        cmd.append(url)
        log(f"Adding URL to command: {url}")

    log(f"Full command: {' '.join(cmd)}")

    try:
        # Start the process and capture any immediate errors
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy(),  # Pass current environment
        )

        # Wait a moment to see if it fails immediately
        try:
            stdout, stderr = process.communicate(timeout=3)
            if process.returncode != 0:
                log(f"Vivaldi failed with return code {process.returncode}")
                log(f"STDOUT: {stdout.decode()}")
                log(f"STDERR: {stderr.decode()}")
                sys.exit(1)
        except subprocess.TimeoutExpired:
            # Process is still running, which is good for GUI apps
            log("Vivaldi process started successfully and is running")

        log(
            f"vivaldi_launch launched Vivaldi with profile {profile}"
            + (f" and URL {url}" if url else "")
        )
    except Exception as e:
        log(f"Error launching Vivaldi: {e}")
        import traceback

        log(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
