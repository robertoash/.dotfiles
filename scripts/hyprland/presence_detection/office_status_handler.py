#!/usr/bin/env python3

# NOTE: This script is currently DISABLED as part of simplifying idle detection
# The advanced idle management has been replaced with simple timeout-based system
# This file is kept for reference but should not be used by hypridle.conf

import logging
import subprocess

# import time
from pathlib import Path

# Configuration
LOG_FILE = Path("/tmp/office_status_handler.log")
PID_FILE = Path("/tmp/office_status_handler.pid")
EXIT_FLAG = Path("/tmp/office_status_handler_exit")
IN_OFFICE_STATUS_FILE = Path("/tmp/mqtt/in_office_status")
DPMS_DELAY = 30  # seconds to wait before turning off displays


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
        subprocess.run(["hyprlock"], check=False)  # Don't fail if already locked
        return True
    except Exception as e:
        logging.error(f"Failed to lock session: {e}")
        return False


def turn_dpms_off():
    """Turn DPMS off using hyprctl."""
    try:
        logging.info("Turning displays off (DPMS off)")
        subprocess.run(["hyprctl", "dispatch", "dpms", "off"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS off: {e}")
        return False


def turn_dpms_on():
    """Turn DPMS on using hyprctl."""
    try:
        logging.info("Turning displays on (DPMS on)")
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
        logging.info("Office status handler exiting")
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")


def main():
    """Main function - monitor office status and handle locking/DPMS."""
    setup_logging()

    # SCRIPT DISABLED - log and exit
    logging.info(
        "Office status handler called but is DISABLED in simplified idle detection mode"
    )
    logging.info(
        "This script has been replaced with simple timeout-based idle detection"
    )
    return

    # The rest of this function is commented out since the script is disabled
    """
    # Clean up our own exit flag if it exists (from previous run)
    EXIT_FLAG.unlink(missing_ok=True)
    logging.debug("Cleaned up any existing exit flag")

    # Create PID file
    try:
        import os

        PID_FILE.write_text(str(os.getpid()))
        logging.info("Office status handler started")
    except Exception as e:
        logging.error(f"Failed to create PID file: {e}")
        return

    try:
        while True:
            # Check for exit signal
            if EXIT_FLAG.exists():
                logging.info("Exit signal received - stopping monitoring")
                break

            office_status = get_in_office_status()

            if office_status == "off":
                logging.info(
                    "in_office turned OFF - would lock but skipping due to hyprlock config issues"
                )
                # lock_session()  # Temporarily disabled due to hyprlock config errors

                # Start DPMS delay immediately after locking
                logging.info(
                    f"Starting {DPMS_DELAY} second countdown before turning off displays"
                )
                start_time = time.time()

                while time.time() - start_time < DPMS_DELAY:
                    # Check if exit signal received
                    if EXIT_FLAG.exists():
                        logging.info(
                            "Exit signal received during DPMS delay - aborting"
                        )
                        return

                    # Check if office status changed back to on
                    if get_in_office_status() == "on":
                        logging.info(
                            "in_office turned back ON during delay - aborting DPMS off"
                        )
                        break

                    time.sleep(1)
                else:
                    # Delay completed and still off
                    if get_in_office_status() == "off":
                        logging.info(
                            "DPMS delay completed and still OFF - turning off displays"
                        )
                        turn_dpms_off()
                    else:
                        logging.info(
                            "Status changed during final check - not turning off displays"
                        )

                # Job done, exit
                break

            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        cleanup()
    """


if __name__ == "__main__":
    main()
