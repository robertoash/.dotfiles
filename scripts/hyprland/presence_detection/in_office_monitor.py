#!/usr/bin/env python3

import logging
import subprocess
import time
from pathlib import Path

# Configuration
IN_OFFICE_STATUS_FILE = Path("/tmp/mqtt/in_office_status")
LOG_FILE = Path("/tmp/in_office_monitor.log")
PID_FILE = Path("/tmp/in_office_monitor.pid")
WORK_HOURS_START = 6
WORK_HOURS_END = 20


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


def is_work_hours():
    """Check if current time is within work hours."""
    current_hour = time.localtime().tm_hour
    return WORK_HOURS_START <= current_hour <= WORK_HOURS_END


def get_in_office_status():
    """Get the current in_office status."""
    try:
        return IN_OFFICE_STATUS_FILE.read_text().strip()
    except FileNotFoundError:
        logging.warning("in_office_status file not found, defaulting to 'on'")
        return "on"


def run_dpms_command(action):
    """Run DPMS command (on/off)."""
    try:
        cmd = ["hyprctl", "dispatch", "dpms", action]
        logging.info(f"Running DPMS command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        logging.info(f"DPMS {action} successful")
    except subprocess.CalledProcessError as e:
        logging.error(f"DPMS command failed: {e}")
    except FileNotFoundError:
        logging.error("hyprctl command not found")


def create_pid_file():
    """Create PID file to track running instance."""
    try:
        import os

        PID_FILE.write_text(str(os.getpid()))
        logging.info(f"Created PID file: {PID_FILE}")
    except Exception as e:
        logging.error(f"Failed to create PID file: {e}")


def cleanup_pid_file():
    """Remove PID file."""
    try:
        PID_FILE.unlink()
        logging.info(f"Removed PID file: {PID_FILE}")
    except FileNotFoundError:
        pass
    except Exception as e:
        logging.error(f"Failed to remove PID file: {e}")


def main():
    """Main monitoring loop."""
    setup_logging()
    logging.info("In-office monitor started")

    create_pid_file()

    try:
        past_status = ""

        while True:
            # Only operate during work hours
            if is_work_hours():
                current_status = get_in_office_status()

                # Only act on status changes to avoid duplicate commands
                if current_status != past_status:
                    logging.info(
                        f"Office status changed: {past_status} -> {current_status}"
                    )

                    if current_status == "on":
                        run_dpms_command("on")
                    elif current_status == "off":
                        run_dpms_command("off")

                    past_status = current_status
            else:
                # Outside work hours, just update past_status if needed
                current_status = get_in_office_status()
                if past_status == "":
                    past_status = current_status
                    logging.debug(
                        f"Outside work hours, current status: {current_status}"
                    )

            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Received interrupt signal, shutting down gracefully")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        cleanup_pid_file()
        logging.info("In-office monitor stopped")


if __name__ == "__main__":
    main()
