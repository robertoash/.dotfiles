#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
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
    prev_state = None



    logging.info("Loading environment variables")
    load_environment_variables()

    while True:
        state = get_state()
        output = {"text": "", "tooltip": "Error fetching state"}

        current_hour = datetime.now().hour
        working_hours = (5 <= current_hour < 19)

        if state:
            if state == "on" and prev_state == "off":
                if working_hours:
                    # dpms on
                    subprocess.check_output("hyprctl dispatch dpms on", shell=True)
            elif state == "off" and prev_state == "on":
                if is_unlocked():
                    # Lock the screen in the background
                    subprocess.Popen(["hyprlock", "-q"])
                    time.sleep(1)
                # Turn off the screen
                subprocess.run(["hyprctl", "dispatch", "dpms off"], check=True)

            output = {
                "text": "󰀈" if state == "on" else "󰀒",
                "tooltip": f"Presence idle_inhibit is {state}",
                "class": "icon-blue" if state == "on" else "icon-red",
            }

            prev_state = state
        else:
            if not is_hypridle_running():
                start_hypridle(error=True)

        if output != last_output:
            with open(output_file, "w") as f:
                json.dump(output, f)
            logging.info(f"Output: {output}")
            last_output = output

        time.sleep(interval)


if __name__ == "__main__":
    logging.info("Script started")
    main()
