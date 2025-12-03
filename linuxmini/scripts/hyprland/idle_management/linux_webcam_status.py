#!/usr/bin/env python3

import argparse
import logging
import subprocess
import sys
import time

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

# Import centralized configuration
from config import (  # noqa: E402
    DEVICE_FILES,
    WEBCAM_CONFIG,
    get_check_interval,
    get_status_file,
    get_system_command,
)

"""
This script is launched by a systemd service.
The service file is here:
  /home/rash/.config/systemd/user/linux-webcam-status.service

Status can be checked with:
  systemctl --user status linux-webcam-status.service
"""

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Monitor webcam status.")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Configure logging
logging_utils.configure_logging()
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.ERROR)

# Get configuration from centralized config
device_file_path = str(DEVICE_FILES["webcam"])
last_state = "inactive"  # Track the last state to avoid duplicate writes
status_file_path = str(get_status_file("linux_webcam_status"))
excluded_processes = WEBCAM_CONFIG["excluded_processes"]
webcam_polling_interval = get_check_interval("webcam_polling")


def is_webcam_in_use():
    """Check if webcam is in use by non-automated processes (excludes configured processes)."""
    try:
        # Get list of processes using the camera
        lsof_command = get_system_command("lsof_webcam") + [device_file_path]
        lsof_output = subprocess.check_output(
            lsof_command, stderr=subprocess.DEVNULL, text=True
        )

        for line in lsof_output.strip().split("\n"):
            if line and not line.startswith("COMMAND"):  # Skip header
                # Check if this line contains any excluded process
                line_lower = line.lower()
                excluded = False
                for process in excluded_processes:
                    if process.lower() in line_lower:
                        logging.debug(f"Ignoring {process} process: {line}")
                        excluded = True
                        break

                if not excluded:
                    # If it's not an excluded process, webcam is in use by something else
                    logging.debug(f"Non-automated webcam usage detected: {line}")
                    return True

        # All processes using camera are excluded - consider inactive
        logging.debug("Only excluded processes using camera - considering inactive")
        return False

    except subprocess.CalledProcessError:
        # No processes using camera
        return False


def update_status_file(state):
    import os

    os.makedirs(os.path.dirname(status_file_path), exist_ok=True)
    with open(status_file_path, "w") as f:
        f.write(state)
    logging.debug(f"Success: {status_file_path} updated - Webcam is {state}")


def main():
    global last_state

    while True:
        try:
            # Wait for webcam to become active
            inotify_command = get_system_command("inotifywait_webcam") + [
                device_file_path
            ]
            subprocess.run(inotify_command, check=True)

            # When inotifywait detects an open event, check if the webcam is actually in use
            if is_webcam_in_use() and last_state == "inactive":
                logging.debug("Webcam is active")
                update_status_file("active")
                last_state = "active"

            # Start polling to detect when the webcam becomes inactive
            while is_webcam_in_use():
                time.sleep(webcam_polling_interval)

            # Once polling detects the webcam is inactive
            if last_state == "active":
                logging.debug("Webcam is inactive")
                update_status_file("inactive")
                last_state = "inactive"
        except subprocess.CalledProcessError as e:
            logging.error(f"Error: {e}")


if __name__ == "__main__":
    main()
