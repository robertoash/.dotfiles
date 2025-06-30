#!/usr/bin/env python3

import logging
import subprocess
import time
from pathlib import Path

# Configuration
LOG_FILE = Path("/tmp/cleanup_on_resume.log")

# Exit flag files for various processes
# NOTE: Face detection and advanced idle management are currently disabled
EXIT_FLAGS = [
    # Path("/tmp/continuous_face_monitor_exit"),  # Disabled - face detection unplugged
    # Path("/tmp/office_status_handler_exit"),   # Disabled - using simple idle management
    # Path("/tmp/face_presence_coordinator_exit"),  # Legacy cleanup - disabled
    # Path("/tmp/in_office_monitor_exit"),  # Monitor runs continuously, no need to stop on resume
]

# Status files to reset
STATUS_FILES = [
    Path("/tmp/mqtt/idle_detection_status"),
    # Path("/tmp/mqtt/face_presence"),  # Disabled - face detection unplugged
]


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


def create_exit_flags():
    """Create exit flag files to signal all monitoring processes to stop."""
    for flag_file in EXIT_FLAGS:
        try:
            flag_file.parent.mkdir(parents=True, exist_ok=True)
            flag_file.write_text(str(time.time()))
            logging.info(f"Created exit flag: {flag_file}")
        except Exception as e:
            logging.error(f"Failed to create exit flag {flag_file}: {e}")


def reset_status_files():
    """Reset status files to normal values."""
    status_updates = {
        Path("/tmp/mqtt/idle_detection_status"): "inactive",
        # Path("/tmp/mqtt/face_presence"): "not_detected",  # Disabled - face detection unplugged
    }

    for status_file, value in status_updates.items():
        try:
            status_file.parent.mkdir(parents=True, exist_ok=True)
            status_file.write_text(value)
            logging.info(f"Reset {status_file} to: {value}")
        except Exception as e:
            logging.error(f"Failed to reset {status_file}: {e}")


def turn_dpms_on():
    """Ensure displays are turned on."""
    try:
        logging.info("Ensuring displays are on (DPMS on)")
        subprocess.run(["hyprctl", "dispatch", "dpms", "on"], check=True)
        logging.info("DPMS on successful")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to turn DPMS on: {e}")
    except FileNotFoundError:
        logging.error("hyprctl command not found")


def report_active_status():
    """Report active status to HA."""
    try:
        logging.info("Reporting active status to HA")
        script = "/home/rash/.config/scripts/ha/activity_status_reporter.py"
        subprocess.run([script, "--active"], check=True)
        logging.info("Active status reported successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to report active status: {e}")
    except FileNotFoundError:
        logging.error("activity_status_reporter.py not found")


def cleanup_exit_flags():
    """Clean up exit flags after processes have stopped."""
    for flag_file in EXIT_FLAGS:
        try:
            flag_file.unlink(missing_ok=True)
            logging.info(f"Cleaned up exit flag: {flag_file}")
        except Exception as e:
            logging.error(f"Failed to clean up exit flag {flag_file}: {e}")


def main():
    """Main cleanup function."""
    setup_logging()
    logging.info(
        "Resume cleanup started - stopping all monitoring processes (simplified)"
    )

    # Create exit flags to stop all monitoring processes
    create_exit_flags()

    # Give processes a moment to see the exit flags and stop gracefully
    time.sleep(2)

    # Clean up the exit flags we just created
    cleanup_exit_flags()

    # Reset status files to active/normal state
    reset_status_files()

    # Ensure displays are on
    turn_dpms_on()

    # Report active status to HA
    report_active_status()

    logging.info(
        "Resume cleanup completed - simplified monitoring stopped and state reset"
    )


if __name__ == "__main__":
    main()
