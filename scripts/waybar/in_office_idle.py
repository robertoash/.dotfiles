#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import sys

import psutil

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.info("Script launched.")


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
        logging.info("Environment variables loaded successfully.")
        logging.info(f"HASS_SERVER: {os.environ.get('HASS_SERVER')}")
        logging.info(f"HASS_TOKEN: {os.environ.get('HASS_TOKEN')}")
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
                "/home/rash/.local/bin/hass-cli state get input_boolean.rob_in_office | awk -F '  +' 'NR==2 {print $3}'",
                shell=True,
            )
            .strip()
            .decode()
        )
        return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting state: {e}")
        return None


def start_inhibit(reason):
    try:
        logging.info(f"Systemd-inhibit started due to: {reason}")
        process = subprocess.Popen(
            [
                "systemd-inhibit",
                "--what=idle",
                f"--why={reason}",
                "bash",
                "-c",
                "sleep infinity",
            ]
        )
        with open("/tmp/inhibit_process.pid", "w") as f:
            f.write(str(process.pid))
        return process
    except Exception as e:
        logging.error(f"Error starting systemd-inhibit: {e}")
        return None


def stop_inhibit(process, reason):
    try:
        logging.info(f"Systemd-inhibit stopped due to: {reason}")
        process.terminate()
        os.remove("/tmp/inhibit_process.pid")
    except Exception as e:
        logging.error(f"Error stopping systemd-inhibit: {e}")


def check_inhibit_process():
    if os.path.exists("/tmp/inhibit_process.pid"):
        with open("/tmp/inhibit_process.pid", "r") as f:
            pid = int(f.read().strip())
            if psutil.pid_exists(pid):
                return psutil.Process(pid)
    return None


def main():
    logging.info("Loading environment variables")
    load_environment_variables()

    inhibit_process = check_inhibit_process()
    state = get_state()
    output = {"text": "󰀒", "tooltip": "Error fetching state", "class": "idle-grey"}

    if state:
        if state == "on" and is_unlocked():
            if not inhibit_process:
                inhibit_process = start_inhibit("User is in the office")
        else:
            if inhibit_process:
                stop_inhibit(inhibit_process, "User is no longer in the office")
                inhibit_process = None
        output = {
            "text": "󰀈" if state == "on" else "󰀒",
            "tooltip": f"Presence idle_inhibit is {state}",
            "class": "idle-blue" if state == "on" else "idle-grey",
        }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
