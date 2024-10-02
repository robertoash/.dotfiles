#!/usr/bin/env python3
import logging
import subprocess
import sys
import time

import requests

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Configure logging
logging_utils.configure_logging()
logging.getLogger().setLevel(logging.INFO)

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def get_mullvad_status():
    try:
        return subprocess.check_output(["mullvad", "status"], text=True)
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
    except FileNotFoundError:
        return "Error: mullvad command not found"


def get_external_ip():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            return requests.get("http://api.ipify.org/?format=text").text.strip()
        except requests.RequestException as e:
            retries += 1
            logging.warning(
                f"Failed to get external IP (attempt {retries}/{MAX_RETRIES}): {e}"
            )
            time.sleep(RETRY_DELAY)
    return "unavailable"


def vpn_is_up(mullvad_status):
    return "Connected" in mullvad_status


try:
    mullvad_status = get_mullvad_status()
    extern_ip = get_external_ip()

    if "Error:" in mullvad_status:
        output = f'{{"text": "?", "tooltip": "{mullvad_status}", "class": "vpn-error"}}'
        print(output)
        logging.error(f"Error getting Mullvad status: {mullvad_status}")
    elif vpn_is_up(mullvad_status):
        output = f'{{"text": "󰕥", "tooltip": "connected. ip is {extern_ip}", "class": "vpn-connected"}}'
        print(output)
        # Log every 10th second
        current_time = int(time.time())
        if current_time % 10 == 0:
            logging.info(output)
    else:
        output = f'{{"text": "", "tooltip": "disconnected. ip is {extern_ip}", "class": "vpn-disconnected"}}'
        print(output)
        # Log every 10th second
        current_time = int(time.time())
        if current_time % 10 == 0:
            logging.info(output)
except Exception as e:
    output = (
        f'{{"text": "!", "tooltip": "Script error: {str(e)}", "class": "vpn-error"}}'
    )
    print(output)
    logging.error(output)

sys.stdout.flush()
