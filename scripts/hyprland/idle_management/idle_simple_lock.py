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
    log_file = get_log_file("idle_simple_lock")

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


def save_and_switch_layout():
    """Save current Kanata layout and switch to Swedish for lock screen."""
    try:
        from pathlib import Path
        
        # Read current layout
        current_layout_file = Path("/tmp/active_keyboard_layout")
        if current_layout_file.exists():
            current_layout = current_layout_file.read_text().strip()
        else:
            current_layout = "cmk"  # Default fallback
        
        # Save current layout for restoration
        saved_layout_file = Path("/tmp/hypridle_saved_layout")
        saved_layout_file.write_text(current_layout)
        logging.info(f"Saved current layout '{current_layout}' for restoration")
        
        # Switch to Swedish nodeadkeys for lock screen
        subprocess.run([
            '/home/rash/.config/scripts/kanata/kanata_layer_switcher.py',
            '--set-layer', 'swe',
            '--set-mod', 'nomod'
        ], check=True, capture_output=True)
        logging.info("Switched to Swedish layout for lock screen")
        
    except Exception as e:
        logging.error(f"Failed to switch layout for lock: {e}")

def lock_session():
    """Lock the session using hyprlock."""
    try:
        # Check if hyprlock is already running
        result = subprocess.run(
            get_system_command("pidof_hyprlock"), capture_output=True
        )
        if result.returncode == 0:
            logging.info("hyprlock already running")
            return True

        # Save and switch Kanata layout before locking
        save_and_switch_layout()

        # Start hyprlock
        logging.info("Locking session with hyprlock")
        subprocess.run(get_system_command("hyprlock"), check=False)
        return True
    except Exception as e:
        logging.error(f"Failed to lock session: {e}")
        return False


def main():
    """Check in_office status and lock if off, or wait for it to turn off."""
    setup_logging()

    # Get control file and check interval from config
    exit_flag = get_control_file("idle_simple_lock_exit")
    check_interval = get_check_interval("lock_monitoring")

    # Clean up our own exit flag if it exists (from previous run)
    exit_flag.unlink(missing_ok=True)

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
            if exit_flag.exists():
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

            time.sleep(check_interval)

    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        # Clean up exit flag
        exit_flag.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
