#!/usr/bin/env python3

import logging
import subprocess
import time
from pathlib import Path

# Configuration
LOG_FILE = Path("/tmp/in_office_monitor.log")
PID_FILE = Path("/tmp/in_office_monitor.pid")
EXIT_FLAG = Path("/tmp/in_office_monitor_exit")
IN_OFFICE_STATUS_FILE = Path("/tmp/mqtt/in_office_status")
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
        return "on"  # Default to on if file doesn't exist


def turn_dpms_on():
    """Turn DPMS on using hyprctl."""
    try:
        logging.info("in_office turned ON - turning displays on (DPMS on)")
        subprocess.run(["hyprctl", "dispatch", "dpms", "on"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS on: {e}")
        return False


def cleanup():
    """Clean up files on exit."""
    try:
        PID_FILE.unlink(missing_ok=True)
        EXIT_FLAG.unlink(missing_ok=True)
        logging.info("In-office monitor exiting")
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")


def main():
    """Monitor in_office status and turn dpms on when it changes to on."""
    setup_logging()

    # Clean up our own exit flag if it exists (from previous run)
    EXIT_FLAG.unlink(missing_ok=True)
    logging.debug("Cleaned up any existing exit flag")

    # Create PID file
    try:
        import os

        PID_FILE.write_text(str(os.getpid()))
        logging.info("In-office monitor started")
    except Exception as e:
        logging.error(f"Failed to create PID file: {e}")
        return

    last_status = get_in_office_status()
    logging.info(f"Initial in_office status: {last_status}")

    try:
        while True:
            # Check for exit signal
            if EXIT_FLAG.exists():
                logging.info("Exit signal received - stopping monitoring")
                break

            current_status = get_in_office_status()

            # If status changed from off to on, turn dpms on
            if last_status == "off" and current_status == "on":
                logging.info("in_office status changed from OFF to ON")
                turn_dpms_on()

            last_status = current_status
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
