#!/usr/bin/env python3

"""
This script is launched by hypridle based on activity.
The config file is here:
/home/rash/.config/hypr/hypridle.conf
"""

import logging
import os
import sys

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.getLogger().setLevel(logging.INFO)

status_file_path = "/tmp/mqtt/linux_mini_status"


def update_status(state):
    os.makedirs(os.path.dirname(status_file_path), exist_ok=True)
    with open(status_file_path, "w") as f:
        f.write(state)
    logging.info(f"Success: {status_file_path} updated - Linux Mini is {state}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["--active", "--inactive"]:
        sys.exit(1)

    state = "active" if sys.argv[1] == "--active" else "inactive"
    update_status(state)
