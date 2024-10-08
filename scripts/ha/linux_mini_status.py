#!/usr/bin/env python3

"""
This script is launched by hypridle based on activity.
The config file is here:
/home/rash/.config/hypr/hypridle.conf
"""

import argparse
import logging
import os
import sys
from datetime import datetime

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils


def parse_args():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Update Linux Mini status.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--active",
        action="store_const",
        const="active",
        dest="state",
        help="Set the state of Linux Mini to active",
    )
    group.add_argument(
        "--inactive",
        action="store_const",
        const="inactive",
        dest="state",
        help="Set the state of Linux Mini to inactive",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.state is None:
        parser.error("One of --active or --inactive is required")

    return args


def configure_logging(debug):
    logging_utils.configure_logging()
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.ERROR)


def update_status(state):

    status_file_path = "/tmp/mqtt/linux_mini_status"

    os.makedirs(os.path.dirname(status_file_path), exist_ok=True)
    with open(status_file_path, "w") as f:
        f.write(state)
    logging.debug(f"Success: {status_file_path} updated - Linux Mini is {state}")


if __name__ == "__main__":
    args = parse_args()
    configure_logging(args.debug)
    update_status(args.state)
