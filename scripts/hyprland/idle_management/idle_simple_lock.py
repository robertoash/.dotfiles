#!/usr/bin/env python3

import logging
import subprocess
import time
from pathlib import Path

# Configuration
LOG_FILE = Path("/tmp/idle_simple_lock.log")
IN_OFFICE_STATUS_FILE = Path("/tmp/mqtt/in_office_status")
EXIT_FLAG = Path("/tmp/idle_simple_lock_exit")
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


def lock_session():
    """Lock the session using hyprlock."""
    try:
        # Check if hyprlock is already running
        result = subprocess.run(["pidof", "hyprlock"], capture_output=True)
        if result.returncode == 0:
            logging.info("hyprlock already running")
            return True

        # Start hyprlock
        logging.info("Locking session with hyprlock")
        subprocess.run(["hyprlock"], check=False)
        return True
    except Exception as e:
        logging.error(f"Failed to lock session: {e}")
        return False


def main():
    """Check in_office status and lock if off, or wait for it to turn off."""
    setup_logging()

    # Clean up our own exit flag if it exists (from previous run)
    EXIT_FLAG.unlink(missing_ok=True)

    office_status = get_in_office_status()
    logging.info(f"60-second timeout reached, in_office status: {office_status}")

    if office_status == "off":
        logging.info("in_office is OFF - locking session immediately")
        lock_session()
        return

    # Office is "on" - wait and monitor for status change to "off"
    logging.info("in_office is ON - monitoring for status change to OFF")

    try:
        while True:
            # Check for exit signal (user resumed activity)
            if EXIT_FLAG.exists():
                logging.info(
                    "Exit signal received - user resumed activity, stopping lock monitoring"
                )
                return

            # Check office status
            current_status = get_in_office_status()

            if current_status == "off":
                logging.info("in_office changed to OFF - locking session")
                lock_session()
                return

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        # Clean up exit flag
        EXIT_FLAG.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
