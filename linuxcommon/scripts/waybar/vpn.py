#!/usr/bin/env python3
import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import time

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


def build_output_immediate(state):
    """Build output without IP lookup for immediate display"""
    base = STATE_MAP.get(state, {"text": "?", "class": "vpn-error"})
    tooltip = state
    if state in ("Connecting", "Disconnecting"):
        tooltip += "..."

    output_data = {
        "text": base["text"],
        "tooltip": tooltip,
        "class": base["class"],
    }
    logging.debug(f"Built immediate output data: {output_data}")
    print(json.dumps(output_data))
    return output_data


def build_output_with_ip(state):
    """Build output with IP lookup for complete information"""
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
    logging.debug(f"Built complete output data: {output_data}")
    print(json.dumps(output_data))
    return output_data


def build_output(state):
    """Build output with immediate update, then IP lookup in background"""
    # First, update immediately without IP lookup
    immediate_output = build_output_immediate(state)
    write_to_file(immediate_output)

    # For connected/disconnected states, fetch IP in background
    if state in ("Connected", "Disconnected"):

        def update_with_ip():
            complete_output = build_output_with_ip(state)
            write_to_file(complete_output)

        # Run IP lookup in background thread
        threading.Thread(target=update_with_ip, daemon=True).start()

    return immediate_output


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
            build_output(new_state)
            last_state = new_state

    proc.stdout.close()
    proc.wait()


def main():
    try:
        # Write loading state immediately so the status file always exists
        # before mullvad status is queried (important at boot where the
        # mullvad-daemon may not be ready yet).
        write_to_file({"text": "󰇘", "tooltip": "Loading...", "class": "vpn-disconnected"})

        # Retry mullvad status — daemon may take a moment to start after boot
        state = None
        for attempt in range(6):
            result = subprocess.run(
                ["mullvad", "status"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                state = "Connected" if "Connected" in result.stdout else "Disconnected"
                logging.info(f"Initial VPN state: {state}")
                build_output(state)
                break
            logging.warning(f"mullvad status attempt {attempt + 1} failed: {result.stderr.strip()}")
            time.sleep(3)

        if state is None:
            logging.error("Could not get initial VPN state after retries")
            write_to_file({"text": "!", "tooltip": "Failed to get VPN state", "class": "vpn-error"})

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
