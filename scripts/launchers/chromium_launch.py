#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# === CONFIGURATION === #
LOG_FILE = Path("/tmp/ungoogled_chromium_direct.log")
CHROMIUM_BIN = "/usr/bin/chromium"  # Verify this path is correct

# Define profiles and how to launch them
PROFILES = {
    "rash": {
        "profile_directory": "rash",
        "app_url": None,
    },
    "jobhunt": {
        "profile_directory": "work",
        "app_url": None,
    },
    "app": {
        "profile_directory": "app",
        "app_url": None,
    },
    "dash": {
        "profile_directory": "dash",
        "app_url": None,
    },
    "chatgpt": {
        "profile_directory": "app",
        "app_url": "https://chat.openai.com",
    },
    "perplexity": {
        "profile_directory": "app",
        "app_url": "https://perplexity.ai",
    },
    "tiktok": {
        "profile_directory": "app",
        "app_url": "https://www.tiktok.com",
    },
    "youtube": {
        "profile_directory": "app",
        "app_url": "https://youtube.com",
    },
    "svtplay": {
        "profile_directory": "app",
        "app_url": "https://svtplay.se",
    },
    "max": {
        "profile_directory": "app",
        "app_url": "https://max.com",
    },
    "overseerr": {
        "profile_directory": "app",
        "app_url": "https://watchlist.rashlab.net",
    },
    "github": {
        "profile_directory": "app",
        "app_url": "https://github.com",
    },
    "claude": {
        "profile_directory": "app",
        "app_url": "https://claude.ai",
    },
    "google_calendar": {
        "profile_directory": "app",
        "app_url": "https://calendar.google.com",
    },
    "ha": {
        "profile_directory": "app",
        "app_url": "https://ha.rashlab.net",
    },
}

# Ungoogled Chromium command-line arguments
BASE_ARGS = [
    "--new-window",
    "--new-instance",
    "--ozone-platform=wayland",
    "--enable-features=UseOzonePlatform",
    # Performance optimizations
    "--disable-background-networking",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
    "--disable-sync",
    "--disable-translate",
    # Minimal UI in app mode
    "--disable-features=TranslateUI",
    "--disable-popup-blocking",
]

# === END CONFIGURATION === #


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a") as f:
        f.write(f"{timestamp}: {message}\n")


def build_command(profile_info: dict) -> list:
    cmd = [CHROMIUM_BIN] + BASE_ARGS
    cmd.append(f"--profile-directory={profile_info['profile_directory']}")
    if profile_info.get("app_url"):
        cmd.append(f"--app={profile_info['app_url']}")
    return cmd


def main():
    # Log execution
    log(f"chromium_launch called with args: {' '.join(sys.argv[1:])}")

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

    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(
            f"chromium_launch launched Ungoogled Chromium with profile {profile}"
            + (f" and URL {url}" if url else "")
        )
    except Exception as e:
        log(f"Error launching Ungoogled Chromium: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
