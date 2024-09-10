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


def is_unlocked():
    try:
        user = subprocess.check_output("whoami").strip().decode()
        session_id = (
            subprocess.check_output(f"loginctl | grep {user}", shell=True)
            .strip()
            .decode()
            .split()[0]
        )
        locked_output = (
            subprocess.check_output(
                f"loginctl show-session {session_id} -p LockedHint", shell=True
            )
            .strip()
            .decode()
        )
        locked = locked_output.split("=")[1]
        return locked == "no"
    except subprocess.CalledProcessError as e:
        logging.error(f"Error checking if unlocked: {e}")
        return False


def get_state():
    try:
        result = (
            subprocess.check_output(
                "/home/rash/.local/bin/hass-cli state get binary_sensor.rob_in_office "
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


def is_hypridle_running():
    try:
        result = subprocess.check_output(["pgrep", "-x", "hypridle"])
        return bool(result.strip())
    except subprocess.CalledProcessError:
        return False


def stop_hypridle():
    try:
        logging.info("Stopping hypridle")
        subprocess.check_call(["pkill", "hypridle"])
    except subprocess.CalledProcessError as e:
        logging.error(f"Error stopping hypridle: {e}")


def start_hypridle(error=False):
    if error:
        config_file = os.path.expanduser("~/.config/hypr/hypridle.conf")
    else:
        config_file = os.path.expanduser("~/.config/hypr/hypridle_immediate.conf")

    try:
        logging.info("Starting hypridle")
        subprocess.Popen(
            [
                "hypridle",
                "-c",
                config_file,
            ]
        )
    except Exception as e:
        logging.error(f"Error starting hypridle: {e}")


def main():
    output_file = "/tmp/in_office_idle_output.json"
    interval = 2  # Interval in seconds
    last_output = None

    logging.info("Loading environment variables")
    load_environment_variables()

    while True:
        state = get_state()
        output = {"text": "", "tooltip": "Error fetching state"}

        if state:
            if state == "on" and is_unlocked():
                if is_hypridle_running():
                    stop_hypridle()
            else:
                if not is_hypridle_running():
                    start_hypridle(error=False)

            output = {
                "text": "󰀈" if state == "on" else "󰀒",
                "tooltip": f"Presence idle_inhibit is {state}",
                "class": "icon-blue" if state == "on" else "icon-red",
            }
        else:
            start_hypridle(error=True)

        if last_output != output:
            with open(output_file, "w") as f:
                json.dump(output, f)
            logging.info(f"Output: {output}")
            last_output = output

        time.sleep(interval)


if __name__ == "__main__":
    logging.info("Script started")
    main()
