#!/usr/bin/env python3

# NOTE: This script is currently DISABLED as part of unplugging face detection
# Face detection has been temporarily disabled while simplifying idle detection
# This file is kept for reference but should not be used by hypridle.conf

import logging

# import subprocess
# import time
from pathlib import Path

# Configuration
LOG_FILE = Path("/tmp/continuous_face_monitor.log")
PID_FILE = Path("/tmp/continuous_face_monitor.pid")
EXIT_FLAG = Path("/tmp/continuous_face_monitor_exit")
FACE_PRESENCE_FILE = Path("/tmp/mqtt/face_presence")


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


def cleanup():
    """Clean up files on exit."""
    try:
        PID_FILE.unlink(missing_ok=True)
        EXIT_FLAG.unlink(missing_ok=True)
        logging.info("Continuous face monitor exiting")
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")


def get_face_status():
    """Get current face detection status."""
    try:
        return FACE_PRESENCE_FILE.read_text().strip()
    except FileNotFoundError:
        return "unknown"


def main():
    """Main function - continuously monitor face detection."""
    setup_logging()

    # SCRIPT DISABLED - log and exit
    logging.info(
        "Continuous face monitor called but is DISABLED - face detection unplugged"
    )
    logging.info(
        "Face detection has been temporarily disabled while simplifying idle detection"
    )
    return

    # The rest of this function is commented out since face detection is disabled
    """
    # Clean up our own exit flag if it exists (from previous run)
    EXIT_FLAG.unlink(missing_ok=True)
    logging.debug("Cleaned up any existing exit flag")

    # Create PID file
    try:
        import os

        PID_FILE.write_text(str(os.getpid()))
        logging.info("Continuous face monitor started")
    except Exception as e:
        logging.error(f"Failed to create PID file: {e}")
        return

    face_detection_process = None

    try:
        # Start face detection
        script = (
            "/home/rash/.config/scripts/hyprland/presence_detection/face_detector.py"
        )
        face_detection_process = subprocess.Popen([script])
        logging.info("Started face detection process")

        while True:
            # Check for exit signal
            if EXIT_FLAG.exists():
                logging.info("Exit signal received - stopping face detection")
                break

                # Check if face detection process died and restart if needed
            if face_detection_process and face_detection_process.poll() is not None:
                face_status = get_face_status()

                if face_status == "not_detected":
                    logging.info("Face detection stopped - no face detected")
                    # Set idle detection status to inactive (detection complete)
                    Path("/tmp/mqtt/idle_detection_status").write_text("inactive")
                    logging.info(
                        "Set idle_detection_status to inactive (detection complete)"
                    )
                    break
                else:
                    # Process died for other reason, restart
                    logging.info("Face detection process died unexpectedly, restarting")
                    face_detection_process = subprocess.Popen([script])

            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        # Kill face detection process if still running
        if face_detection_process and face_detection_process.poll() is None:
            face_detection_process.terminate()
            logging.info("Terminated face detection process")
        cleanup()
    """


if __name__ == "__main__":
    main()
