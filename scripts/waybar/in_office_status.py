#!/usr/bin/env python3

import json
import logging
import os
import sys
import time

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.getLogger().setLevel(logging.INFO)


def read_status():
    try:
        with open("/tmp/mqtt/in_office_status", "r") as f:
            return f.read().strip()
    except Exception as e:
        logging.error(f"Error reading status file: {e}")
        return None


def main():
    output_file = "/tmp/waybar/in_office_idle_output.json"
    interval = 1  # Interval in seconds
    last_output = None

    logging.info("Starting in_office_status monitoring")

    while True:
        state = read_status()
        output = {"text": "", "tooltip": "Error fetching state"}

        if state:
            output = {
                "text": "󰀈" if state == "on" else "󰀒",
                "tooltip": f"Presence idle_inhibit is {state}",
                "class": "icon-blue" if state == "on" else "icon-red",
            }

        if output != last_output:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, "w") as f:
                json.dump(output, f)
            logging.info(f"Output: {output}")
            last_output = output
            logging.info(f"Output: {output}")

        time.sleep(interval)


if __name__ == "__main__":
    logging.info("Script started")
    main()
