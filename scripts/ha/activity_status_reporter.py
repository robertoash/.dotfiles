#!/usr/bin/env python3

import datetime
import os
import sys


def log_action(action):
    """Log the action with timestamp for debugging."""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("/tmp/mini_status_debug.log", "a") as f:
            f.write(f"{timestamp} - {action}\n")
    except Exception as e:
        print(f"Logging failed: {e}")


def main():
    # Ensure the mqtt directory exists
    os.makedirs("/tmp/mqtt", exist_ok=True)

    log_action(f"Script called with args: {sys.argv}")

    if "--active" in sys.argv:
        log_action("Setting statuses to ACTIVE")
        # Set mini status to active
        with open("/tmp/mqtt/linux_mini_status", "w") as f:
            f.write("active")

        # Set idle detection to inactive (not running)
        with open("/tmp/mqtt/idle_detection_status", "w") as f:
            f.write("inactive")

    elif "--inactive" in sys.argv:
        log_action("Setting statuses to INACTIVE and starting presence check")
        # Set mini status to inactive
        with open("/tmp/mqtt/linux_mini_status", "w") as f:
            f.write("inactive")

        # Set idle detection to in_progress (starting presence checking phase)
        with open("/tmp/mqtt/idle_detection_status", "w") as f:
            f.write("in_progress")
    else:
        log_action("No valid arguments provided")


if __name__ == "__main__":
    main()
