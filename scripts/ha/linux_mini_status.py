#!/usr/bin/env python3

"""
This script is launched by hypridle based on activity.
The config file is here:
/home/rash/.config/hypr/hypridle.conf
"""

import logging
import sys

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.getLogger().setLevel(logging.INFO)


def update_status(state):
    with open("/tmp/linux_mini_status", "w") as f:
        f.write(state)
    logging.info(f"Success: /tmp/linux_mini_status updated - Linux Mini is {state}")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["--active", "--inactive"]:
        sys.exit(1)

    state = "active" if sys.argv[1] == "--active" else "inactive"
    update_status(state)
