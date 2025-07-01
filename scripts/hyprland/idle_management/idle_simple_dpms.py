#!/usr/bin/env python3

import logging
import subprocess
import time

# Import centralized configuration
from config import (
    LOGGING_CONFIG,
    get_check_interval,
    get_control_file,
    get_log_file,
    get_status_file,
    get_system_command,
)


def setup_logging():
    """Set up logging."""
    log_file = get_log_file("idle_simple_dpms")

    logging.basicConfig(
        level=logging.INFO,
        format=LOGGING_CONFIG["format"],
        datefmt=LOGGING_CONFIG["date_format"],
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def get_in_office_status():
    """Get the current in_office status."""
    status_file = get_status_file("in_office_status")
    try:
        return status_file.read_text().strip()
    except FileNotFoundError:
        logging.warning("in_office_status file not found, assuming 'on'")
        return "on"


def turn_dpms_off():
    """Turn DPMS off using hyprctl."""
    try:
        logging.info("Turning displays off (DPMS off)")
        subprocess.run(get_system_command("hyprctl_dpms_off"), check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS off: {e}")
        return False


def main():
    """Check in_office status and turn dpms off if off, or wait for it to turn off."""
    setup_logging()

    # Get control file and check interval from config
    exit_flag = get_control_file(
        "idle_simple_lock_exit"
    )  # Reuse the same exit flag as lock script
    check_interval = get_check_interval("dpms_monitoring")

    office_status = get_in_office_status()
    logging.info(f"120-second timeout reached, in_office status: {office_status}")

    if office_status == "off":
        logging.info("in_office is OFF - turning displays off immediately")
        turn_dpms_off()
        return

    # Office is "on" - wait and monitor for status change to "off"
    logging.info("in_office is ON - monitoring for status change to OFF")

    try:
        while True:
            # Check for exit signal (user resumed activity)
            if exit_flag.exists():
                logging.info(
                    "Exit signal received - user resumed activity, stopping DPMS monitoring"
                )
                return

            # Check office status
            current_status = get_in_office_status()

            if current_status == "off":
                logging.info("in_office changed to OFF - turning displays off")
                turn_dpms_off()
                return

            time.sleep(check_interval)

    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
