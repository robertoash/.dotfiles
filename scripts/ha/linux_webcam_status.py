#!/usr/bin/env python3

import argparse
import logging
import os
import subprocess
import sys
import time

"""
This script is launched by a systemd service.
The service file is here:
  /home/rash/.config/systemd/user/linux-webcam-status.service

Status can be checked with:
  systemctl --user status linux-webcam-status.service
"""

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

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

device_file_path = "/dev/video0"
last_state = "inactive"  # Track the last state to avoid duplicate writes
status_file_path = "/tmp/mqtt/linux_webcam_status"


def is_webcam_in_use():
    try:
        subprocess.check_output(["lsof", device_file_path], stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def update_status_file(state):
    os.makedirs(os.path.dirname(status_file_path), exist_ok=True)
    with open(status_file_path, "w") as f:
        f.write(state)
    logging.debug(f"Success: {status_file_path} updated - Webcam is {state}")


def main():
    global last_state

    while True:
        try:
            # Wait for webcam to become active
            subprocess.run(["inotifywait", "-e", "open", device_file_path], check=True)

            # When inotifywait detects an open event, check if the webcam is actually in use
            if is_webcam_in_use() and last_state == "inactive":
                logging.debug("Webcam is active")
                update_status_file("active")
                last_state = "active"

            # Start polling every 2 seconds to detect when the webcam becomes inactive
            while is_webcam_in_use():
                time.sleep(2)

            # Once polling detects the webcam is inactive
            if last_state == "active":
                logging.debug("Webcam is inactive")
                update_status_file("inactive")
                last_state = "inactive"
        except subprocess.CalledProcessError as e:
            logging.error(f"Error: {e}")


if __name__ == "__main__":
    main()
