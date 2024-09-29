#!/usr/bin/env python3

import logging
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

# Configure logging
logging_utils.configure_logging()
logging.getLogger().setLevel(logging.INFO)

DEVICE_FILE = "/dev/video0"
STATUS_FILE = "/tmp/linux_webcam_status"
LAST_STATE = "inactive"  # Track the last state to avoid duplicate writes


def is_webcam_in_use():
    try:
        subprocess.check_output(["lsof", DEVICE_FILE], stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error: {e}")
        return False


def update_status_file(state):
    with open(STATUS_FILE, "w") as f:
        f.write(state)
    logging.info(f"Success: {STATUS_FILE} updated - Webcam is {state}")


def main():
    global LAST_STATE

    while True:
        try:
            # Wait for webcam to become active
            subprocess.run(["inotifywait", "-e", "open", DEVICE_FILE], check=True)

            # When inotifywait detects an open event, check if the webcam is actually in use
            if is_webcam_in_use() and LAST_STATE == "inactive":
                logging.info("Webcam is active")
                update_status_file("active")
                LAST_STATE = "active"

            # Start polling every 2 seconds to detect when the webcam becomes inactive
            while is_webcam_in_use():
                time.sleep(2)

            # Once polling detects the webcam is inactive
            if LAST_STATE == "active":
                logging.info("Webcam is inactive")
                update_status_file("inactive")
                LAST_STATE = "inactive"
        except subprocess.CalledProcessError as e:
            logging.error(f"Error: {e}")


if __name__ == "__main__":
    main()
