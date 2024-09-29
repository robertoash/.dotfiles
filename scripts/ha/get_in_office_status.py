#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import sys
import time

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.getLogger().setLevel(logging.INFO)


def load_environment_variables():
    try:
        result = (
            subprocess.check_output(
                "/home/rash/.config/scripts/shell/secure_env_secrets.py", shell=True
            )
            .strip()
            .decode()
        )
        for line in result.split("\n"):
            if line.startswith("export "):
                key, value = line[len("export ") :].split("=", 1)
                os.environ[key] = value.strip('"')
    except subprocess.CalledProcessError as e:
        logging.error(f"Error loading environment variables: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while loading environment variables: {e}")


def get_state():
    try:
        result = (
            subprocess.check_output(
                "/home/rash/.local/bin/hass-cli state get input_boolean.rob_in_office "
                "| awk -F '  +' 'NR==2 {print $3}'",
                shell=True,
            )
            .strip()
            .decode()
        )
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting state: {e}")
        return None


def main():
    output_file = "/tmp/in_office_idle_output.json"
    pure_status_file = "/tmp/in_office_pure_status"
    interval = 1  # Interval in seconds
    last_output = None

    logging.info("Loading environment variables")
    load_environment_variables()

    while True:
        state = get_state()
        output = {"text": "", "tooltip": "Error fetching state"}

        if state:
            output = {
                "text": "󰀈" if state == "on" else "󰀒",
                "tooltip": f"Presence idle_inhibit is {state}",
                "class": "icon-blue" if state == "on" else "icon-red",
            }

        if output != last_output:
            with open(output_file, "w") as f:
                json.dump(output, f)
            logging.info(f"Output: {output}")
            last_output = output

        with open(pure_status_file, "w") as f:
            f.write(state)

        time.sleep(interval)


if __name__ == "__main__":
    logging.info("Script started")
    main()
