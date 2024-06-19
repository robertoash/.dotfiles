#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import sys

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.info("Script launched.")


# Function to load environment variables
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


# Function to check if the computer is unlocked
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


# Function to get the state of input_boolean.rob_in_office
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


# Load environment variables
logging.info("Loading environment variables")
load_environment_variables()

# Check the state and print the JSON output
state = get_state()
if state:
    print(
        json.dumps(
            {
                "text": "󰀈" if state == "on" else "󰀒",
                "tooltip": f"Presence idle_inhibit is {state}",
                "class": "idle-blue" if state == "on" else "idle-grey",
            }
        )
    )
