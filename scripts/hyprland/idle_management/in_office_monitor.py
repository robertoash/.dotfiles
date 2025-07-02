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
    is_within_work_hours,
)


def setup_logging():
    """Set up logging."""
    log_file = get_log_file("in_office_monitor")

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
        return "on"  # Default to on if file doesn't exist


def turn_dpms_on():
    """Turn DPMS on using hyprctl, but only during work hours."""
    if not is_within_work_hours():
        logging.info(
            "in_office turned ON - but outside work hours, not turning displays on"
        )
        return True

    try:
        logging.info("in_office turned ON - turning displays on (DPMS on)")
        subprocess.run(get_system_command("hyprctl_dpms_on"), check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS on: {e}")
        return False


def turn_dpms_off():
    """Turn DPMS off using hyprctl."""
    try:
        logging.info("in_office turned OFF - turning displays off (DPMS off)")
        subprocess.run(get_system_command("hyprctl_dpms_off"), check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS off: {e}")
        return False


def cleanup():
    """Clean up files on exit."""
    try:
        pid_file = get_control_file("in_office_monitor_pid")
        exit_flag = get_control_file("in_office_monitor_exit")

        pid_file.unlink(missing_ok=True)
        exit_flag.unlink(missing_ok=True)
        logging.info("In-office monitor exiting")
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")


def main():
    """Monitor in_office status and control DPMS based on status changes."""
    setup_logging()

    # Get control files and check interval from config
    exit_flag = get_control_file("in_office_monitor_exit")
    pid_file = get_control_file("in_office_monitor_pid")
    check_interval = get_check_interval("office_monitoring")

    # Clean up our own exit flag if it exists (from previous run)
    exit_flag.unlink(missing_ok=True)
    logging.debug("Cleaned up any existing exit flag")

    # Create PID file
    try:
        import os

        pid_file.write_text(str(os.getpid()))
        logging.info("In-office monitor started")
    except Exception as e:
        logging.error(f"Failed to create PID file: {e}")
        return

    last_status = get_in_office_status()
    logging.info(f"Initial in_office status: {last_status}")

    try:
        while True:
            # Check for exit signal
            if exit_flag.exists():
                logging.info("Exit signal received - stopping monitoring")
                break

            current_status = get_in_office_status()

            # Handle status transitions in both directions
            if last_status == "off" and current_status == "on":
                logging.info("in_office status changed from OFF to ON")
                turn_dpms_on()
            elif last_status == "on" and current_status == "off":
                logging.info("in_office status changed from ON to OFF")
                turn_dpms_off()

            last_status = current_status
            time.sleep(check_interval)

    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()
