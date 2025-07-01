#!/usr/bin/env python3

import logging
import subprocess
import time

# Import centralized configuration
from config import (
    EXTERNAL_SCRIPTS,
    LOGGING_CONFIG,
    RESUME_DELAYS,
    get_control_file,
    get_log_file,
    get_system_command,
)


def setup_logging():
    """Set up logging."""
    log_file = get_log_file("idle_simple_resume")

    logging.basicConfig(
        level=logging.INFO,
        format=LOGGING_CONFIG["format"],
        datefmt=LOGGING_CONFIG["date_format"],
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def turn_dpms_on():
    """Ensure displays are turned on."""
    try:
        logging.info("Ensuring displays are on (DPMS on)")
        subprocess.run(get_system_command("hyprctl_dpms_on"), check=True)
        logging.info("DPMS on successful")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS on: {e}")
    except FileNotFoundError:
        logging.error("hyprctl command not found")


def report_active_status():
    """Report active status to HA."""
    try:
        logging.info("Reporting active status to HA")
        script = str(EXTERNAL_SCRIPTS["activity_status_reporter"])
        subprocess.run([script, "--active"], check=True)
        logging.info("Active status reported successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to report active status: {e}")
    except FileNotFoundError:
        logging.error("activity_status_reporter.py not found")


def main():
    """Simple resume cleanup - report active and ensure dpms is on."""
    setup_logging()
    logging.info("Simple resume cleanup started")

    # Get control file and delay from config
    lock_exit_flag = get_control_file("idle_simple_lock_exit")
    cleanup_delay = RESUME_DELAYS["exit_flag_cleanup"]

    # Signal any running lock monitoring to stop
    try:
        lock_exit_flag.write_text("resume")
        logging.info("Created exit flag for idle_simple_lock")
    except Exception as e:
        logging.warning(f"Could not create lock exit flag: {e}")

    # Ensure displays are on (in case they were turned off)
    turn_dpms_on()

    # Report active status to HA
    report_active_status()

    # Clean up the exit flag after a moment
    try:
        time.sleep(cleanup_delay)
        lock_exit_flag.unlink(missing_ok=True)
        logging.info("Cleaned up lock exit flag")
    except Exception as e:
        logging.warning(f"Could not clean up lock exit flag: {e}")

    logging.info("Simple resume cleanup completed")
    # Note: in_office_monitor runs continuously, no need to manage it here


if __name__ == "__main__":
    main()
