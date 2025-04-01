#!/usr/bin/env python3
import argparse
import json
import logging
import os
import subprocess
import sys

import requests

sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

# CLI args
parser = argparse.ArgumentParser(
    description="VPN status (event-driven + IP) for Waybar"
)
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Logging
logging_utils.configure_logging()
logging.getLogger().setLevel(logging.DEBUG if args.debug else logging.WARNING)

output_file = "/tmp/waybar/vpn_status_output.json"
IP_TIMEOUT = 5

STATE_MAP = {
    "Connected": {
        "text": "󰕥",
        "class": "vpn-connected",
    },
    "Connecting": {
        "text": "󰇘",
        "class": "vpn-disconnected",
    },
    "Disconnecting": {
        "text": "󰗼",
        "class": "vpn-disconnected",
    },
    "Disconnected": {
        "text": "",
        "class": "vpn-disconnected",
    },
}


def write_to_file(data):
    logging.debug(f"Attempting to write data to {output_file}")
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        logging.debug("Directory created/verified")
        with open(output_file, "w") as f:
            json.dump(data, f)
            logging.info(f"Successfully wrote data: {data}")
    except Exception as e:
        logging.error(f"Error writing to file: {e}")
        raise


def get_external_ip():
    try:
        return requests.get(
            "http://api.ipify.org/?format=text", timeout=IP_TIMEOUT
        ).text.strip()
    except Exception as e:
        logging.warning(f"Could not fetch external IP: {e}")
        return "unknown"


def parse_state_from_log(line):
    if "New tunnel state:" in line:
        for state in STATE_MAP:
            if f"New tunnel state: {state}" in line:
                return state
    return None


def build_output(state):
    base = STATE_MAP.get(state, {"text": "?", "class": "vpn-error"})
    tooltip = state
    if state in ("Connected", "Disconnected"):
        ip = get_external_ip()
        tooltip += f". IP is {ip}"
    else:
        tooltip += "..."

    output_data = {
        "text": base["text"],
        "tooltip": tooltip,
        "class": base["class"],
    }
    logging.debug(f"Built output data: {output_data}")
    print(json.dumps(output_data))
    return output_data


def monitor_logs():
    logging.debug("Starting journalctl -f for mullvad-daemon...")
    cmd = ["journalctl", "-f", "-u", "mullvad-daemon.service", "-o", "cat"]
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
    )

    last_state = None

    for line in iter(proc.stdout.readline, ""):
        line = line.strip()
        logging.debug(f"Log: {line}")
        new_state = parse_state_from_log(line)
        if new_state and new_state != last_state:
            logging.debug(f"Detected VPN state change → {new_state}")
            output = build_output(new_state)
            write_to_file(output)
            last_state = new_state

    proc.stdout.close()
    proc.wait()


def main():
    try:
        # Get initial state
        result = subprocess.run(
            ["mullvad", "status"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            state = "Connected" if "Connected" in result.stdout else "Disconnected"
            logging.info(f"Initial VPN state: {state}")
            output = build_output(state)
            write_to_file(output)
        else:
            logging.error(f"Failed to get initial state: {result.stderr}")
            write_to_file(
                {
                    "text": "!",
                    "tooltip": "Failed to get VPN state",
                    "class": "vpn-error",
                }
            )

        monitor_logs()
    except Exception as e:
        logging.exception("Error in log monitoring")
        write_to_file(
            {
                "text": "!",
                "tooltip": f"Script error: {str(e)}",
                "class": "vpn-error",
            }
        )


if __name__ == "__main__":
    main()
