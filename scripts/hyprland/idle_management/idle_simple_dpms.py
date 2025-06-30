#!/usr/bin/env python3

import logging
import subprocess
import time
from pathlib import Path

# Configuration
LOG_FILE = Path("/tmp/idle_simple_dpms.log")
IN_OFFICE_STATUS_FILE = Path("/tmp/mqtt/in_office_status")
EXIT_FLAG = Path(
    "/tmp/idle_simple_lock_exit"
)  # Reuse the same exit flag as lock script
CHECK_INTERVAL = 1  # seconds


def setup_logging():
    """Set up logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(),
        ],
    )


def get_in_office_status():
    """Get the current in_office status."""
    try:
        return IN_OFFICE_STATUS_FILE.read_text().strip()
    except FileNotFoundError:
        logging.warning("in_office_status file not found, assuming 'on'")
        return "on"


def turn_dpms_off():
    """Turn DPMS off using hyprctl."""
    try:
        logging.info("Turning displays off (DPMS off)")
        subprocess.run(["hyprctl", "dispatch", "dpms", "off"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS off: {e}")
        return False


def main():
    """Check in_office status and turn dpms off if off, or wait for it to turn off."""
    setup_logging()

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
            if EXIT_FLAG.exists():
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

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
