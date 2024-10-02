#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
import sys
import time

import requests

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Parse command-line arguments
parser = argparse.ArgumentParser(description="VPN status script for Waybar")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Configure logging
logging_utils.configure_logging()
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.ERROR)

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

output_file = "/tmp/waybar/vpn_status_output.json"


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


def write_to_file(output):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        f.write(output)


error_message = None

while True:
    try:
        mullvad_status = get_mullvad_status()
        extern_ip = get_external_ip()

        if "Error:" not in mullvad_status:
            if "Connected" in mullvad_status:
                output = f'{{"text": "󰕥", "tooltip": "connected. ip is {extern_ip}", "class": "vpn-connected"}}'
            else:
                output = f'{{"text": "", "tooltip": "disconnected. ip is {extern_ip}", "class": "vpn-disconnected"}}'
        else:
            output = (
                f'{{"text": "?", "tooltip": "{mullvad_status}", "class": "vpn-error"}}'
            )
            error_message = f"Error getting Mullvad status: {mullvad_status}"
        time.sleep(1)

    except Exception as e:
        output = f'{{"text": "!", "tooltip": "Script error: {str(e)}", "class": "vpn-error"}}'
        error_message = f"Script error: {str(e)}"

    write_to_file(output)

    # Log every 10th second
    current_time = int(time.time())
    if current_time % 10 == 0:
        if error_message is None:
            logging.debug(output)
        else:
            logging.error(error_message)
