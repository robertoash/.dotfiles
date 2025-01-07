#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
import sys
import time
import json

import requests

sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

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
poll_interval = 1  # seconds


def get_mullvad_status():
    try:
        return subprocess.check_output(["mullvad", "status"], text=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing 'mullvad status': {e}")
        return None
    except FileNotFoundError:
        logging.error("Mullvad command not found")
        return None


def get_external_ip():
    retries = 0
    while retries < MAX_RETRIES:
        try:
            return requests.get(
                "http://api.ipify.org/?format=text", timeout=5
            ).text.strip()
        except requests.RequestException as e:
            retries += 1
            logging.warning(
                f"Failed to get external IP (attempt {retries}/{MAX_RETRIES}): {e}"
            )
            time.sleep(RETRY_DELAY)
    logging.error("Unable to fetch external IP after retries")
    return "unavailable"


def write_to_file(output_data):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(output_data, f)


def parse_mullvad_status(status):
    if "Connected" in status:
        return "connected"
    elif "Disconnecting" in status:
        return "disconnecting"
    elif "Connecting" in status:
        return "connecting"
    elif "Disconnected" in status:
        return "disconnected"
    return "error"


def main():
    last_status = None

    while True:
        try:
            mullvad_status = get_mullvad_status()
            if mullvad_status is None:
                output = {
                    "text": "?",
                    "tooltip": "Error getting Mullvad status",
                    "class": "vpn-error",
                }
            else:
                connection_status = parse_mullvad_status(mullvad_status)
                extern_ip = get_external_ip()

                if connection_status == "connected":
                    output = {
                        "text": "󰕥",
                        "tooltip": f"Connected. IP is {extern_ip}",
                        "class": "vpn-connected",
                    }
                elif connection_status == "connecting":
                    output = {
                        "text": "󰇘",
                        "tooltip": "Connecting to VPN...",
                        "class": "vpn-disconnected",
                    }
                elif connection_status == "disconnecting":
                    output = {
                        "text": "󰗼",
                        "tooltip": "Disconnecting from VPN...",
                        "class": "vpn-disconnected",
                    }
                elif connection_status == "disconnected":
                    output = {
                        "text": "",
                        "tooltip": f"Disconnected. IP is {extern_ip}",
                        "class": "vpn-disconnected",
                    }
                else:
                    output = {
                        "text": "?",
                        "tooltip": "Unknown Mullvad status",
                        "class": "vpn-error",
                    }

            # Update file only if status has changed
            if output != last_status:
                write_to_file(output)
                last_status = output

            time.sleep(poll_interval)

        except Exception as e:
            logging.exception("Unhandled error in main loop")
            error_output = {
                "text": "!",
                "tooltip": f"Script error: {str(e)}",
                "class": "vpn-error",
            }
            write_to_file(error_output)
            time.sleep(poll_interval)


if __name__ == "__main__":
    main()
