#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import sys
import time

import psutil

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.getLogger().setLevel(logging.ERROR)


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


def start_hypridle():
    try:
        process = subprocess.Popen(
            ["hypridle", "-c", os.path.expanduser("~/.config/hypr/hypridle.conf")]
        )
        with open("/tmp/hypridle_process.pid", "w") as f:
            f.write(str(process.pid))
        return process
    except Exception as e:
        logging.error(f"Error starting hypridle: {e}")
        return None


def stop_hypridle():
    try:
        subprocess.check_call(["pkill", "hypridle"])
        if os.path.exists("/tmp/hypridle_process.pid"):
            os.remove("/tmp/hypridle_process.pid")
    except Exception as e:
        logging.error(f"Error stopping hypridle: {e}")


def check_hypridle_process():
    if os.path.exists("/tmp/hypridle_process.pid"):
        with open("/tmp/hypridle_process.pid", "r") as f:
            pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                return psutil.Process(pid)
    return None


def main():
    output_file = "/tmp/in_office_idle_output.json"
    interval = 2  # Interval in seconds
    last_output = None

    logging.info("Loading environment variables")
    load_environment_variables()

    while True:
        hypridle_process = check_hypridle_process()
        state = get_state()
        output = {"text": "󰀒", "tooltip": "Error fetching state", "class": "idle-grey"}

        if state:
            if state == "on" and is_unlocked():
                if not hypridle_process:
                    hypridle_process = start_hypridle()
            else:
                if hypridle_process:
                    stop_hypridle()
                    hypridle_process = None
            output = {
                "text": "󰀈" if state == "on" else "󰀒",
                "tooltip": f"Presence idle_inhibit is {state}",
                "class": "idle-blue" if state == "on" else "idle-grey",
            }

        if last_output != output:
            with open(output_file, "w") as f:
                json.dump(output, f)
            logging.info(f"Output: {output}")
            last_output = output

        time.sleep(interval)


if __name__ == "__main__":
    main()
