#!/usr/bin/env python3

import datetime
import sys

# Import centralized configuration
from config import ensure_directories, get_log_file, get_status_file


def log_action(action):
    """Log the action with timestamp for debugging."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = get_log_file("activity_status_reporter")
        with open(log_file, "a") as f:
            f.write(f"{timestamp} - {action}\n")
    except Exception as e:
        print(f"Logging failed: {e}")


def main():
    # Ensure the mqtt directory exists
    ensure_directories()

    log_action(f"Script called with args: {sys.argv}")

    if "--active" in sys.argv:
        log_action("Setting statuses to ACTIVE")
        # Set mini status to active
        status_file = get_status_file("linux_mini_status")
        with open(status_file, "w") as f:
            f.write("active")

        # Set idle detection to inactive (not running)
        status_file = get_status_file("idle_detection_status")
        with open(status_file, "w") as f:
            f.write("inactive")

    elif "--inactive" in sys.argv:
        log_action("Setting statuses to INACTIVE and starting presence check")
        # Set mini status to inactive
        status_file = get_status_file("linux_mini_status")
        with open(status_file, "w") as f:
            f.write("inactive")

        # Set idle detection to in_progress (starting presence checking phase)
        status_file = get_status_file("idle_detection_status")
        with open(status_file, "w") as f:
            f.write("in_progress")
    else:
        log_action("No valid arguments provided")


if __name__ == "__main__":
    main()
