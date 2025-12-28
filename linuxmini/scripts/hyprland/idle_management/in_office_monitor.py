#!/usr/bin/env python3

import logging
import os
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
        env = os.environ.copy()
        subprocess.run(get_system_command("hyprctl_dpms_on"), check=True, env=env)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS on: {e}")
        return False


def turn_dpms_off():
    """Turn DPMS off using hyprctl and turn off Home Assistant devices."""
    try:
        logging.info("Turning displays off (DPMS off)")
        env = os.environ.copy()
        subprocess.run(get_system_command("hyprctl_dpms_off"), check=True, env=env)

        # Turn off Home Assistant devices
        logging.info("Turning off Home Assistant devices")
        subprocess.run(
            ["hass-cli", "service", "call", "switch.turn_off",
             "--arguments", "entity_id=switch.robs_office_big_lamp"],
            check=False,
            env=env
        )
        subprocess.run(
            ["hass-cli", "service", "call", "switch.turn_off",
             "--arguments", "entity_id=switch.box"],
            check=False,
            env=env
        )

        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS off: {e}")
        return False


def lock_computer():
    """Lock the computer using hyprlock."""
    try:
        # Check if hyprlock is already running
        result = subprocess.run(
            get_system_command("pidof_hyprlock"), capture_output=True
        )
        if result.returncode == 0:
            logging.info("hyprlock already running")
            return True

        logging.info("Locking computer with hyprlock")
        env = os.environ.copy()
        subprocess.Popen(get_system_command("hyprlock"), env=env)
        return True
    except Exception as e:
        logging.error(f"Failed to lock computer: {e}")
        return False


def is_locked():
    """Check if the computer is locked (hyprlock is running)."""
    try:
        result = subprocess.run(
            get_system_command("pidof_hyprlock"), capture_output=True
        )
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Failed to check lock status: {e}")
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
                # Lock the computer immediately
                lock_computer()

                # Give hyprlock a few seconds to initialize and start rendering
                logging.info("Giving hyprlock 3 seconds to initialize...")
                time.sleep(3)

                # Wait 30 seconds with lock screen visible before turning off DPMS
                logging.info("Waiting 30 seconds before turning off DPMS...")
                time.sleep(30)

                # Check if still OFF and locked before turning off DPMS
                current_status_after_wait = get_in_office_status()
                if current_status_after_wait == "off" and is_locked():
                    logging.info("Still OFF and locked - turning off DPMS")
                    turn_dpms_off()
                elif current_status_after_wait == "on":
                    logging.info("Status changed to ON during wait - skipping DPMS off")
                elif not is_locked():
                    logging.info("Computer is not locked - skipping DPMS off")

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
