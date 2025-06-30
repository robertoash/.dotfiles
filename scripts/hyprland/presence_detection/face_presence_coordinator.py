#!/usr/bin/env python3

import logging
import subprocess
import time
from pathlib import Path

# Constants - face_presence_coordinator.py is called at 60s idle time
FACE_DETECTION_START_TIME = 0  # Start face detection immediately when called
MONITORING_START_TIME = 10  # Enter monitoring mode after initial face detection window

FACE_PRESENCE_COORDINATOR_FLAG = Path("/tmp/face_presence_coordinator_running")
FACE_PRESENCE_COORDINATOR_EXIT_FLAG = Path("/tmp/face_presence_coordinator_exit")
IDLE_DETECTION_STATUS_FILE = Path("/tmp/mqtt/idle_detection_status")
FACE_PRESENCE_FILE = Path("/tmp/mqtt/face_presence")


def setup_logging():
    """Set up logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler("/tmp/face_presence_coordinator.log"),
            logging.StreamHandler(),
        ],
    )


def report_idle_detection_status(status):
    """Report idle detection status to MQTT."""
    logging.info(f"Idle detection status: {status}")
    IDLE_DETECTION_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    IDLE_DETECTION_STATUS_FILE.write_text(status)


def create_flag_file():
    """Create flag file to signal face presence coordinator is running."""
    FACE_PRESENCE_COORDINATOR_FLAG.parent.mkdir(parents=True, exist_ok=True)
    FACE_PRESENCE_COORDINATOR_FLAG.write_text(str(time.time()))
    logging.debug(f"Created flag file: {FACE_PRESENCE_COORDINATOR_FLAG}")


def cleanup_flag_file():
    """Remove flag file to signal face presence coordinator has stopped."""
    try:
        FACE_PRESENCE_COORDINATOR_FLAG.unlink()
        logging.debug(f"Removed flag file: {FACE_PRESENCE_COORDINATOR_FLAG}")
    except FileNotFoundError:
        pass


def should_exit():
    """Check if we should exit gracefully."""
    return FACE_PRESENCE_COORDINATOR_EXIT_FLAG.exists()


def get_face_detection_status():
    """Get the face detection status."""
    try:
        return FACE_PRESENCE_FILE.read_text().strip()
    except FileNotFoundError:
        return "not_detected"


def get_in_office_status():
    """Get the in_office status."""
    try:
        status_file = Path("/tmp/mqtt/in_office_status")
        return status_file.read_text().strip()
    except FileNotFoundError:
        return "on"


def run_command(command):
    """Run a shell command."""
    try:
        logging.info(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
    except FileNotFoundError:
        logging.error(f"Command not found: {command[0]}")


def main():
    """Main function."""
    setup_logging()
    logging.info("Face presence coordinator started.")

    # Create flag file and report that idle detection is starting
    create_flag_file()
    report_idle_detection_status("in_progress")

    try:
        start_time = time.time()
        face_detection_process = None

        while True:
            elapsed_time = time.time() - start_time

            # Check for exit signal
            if should_exit():
                logging.info("Exit signal received. Exiting gracefully.")
                if face_detection_process:
                    face_detection_process.kill()
                break

            # --- Stage 1: Face Detection Window ---
            if FACE_DETECTION_START_TIME <= elapsed_time < MONITORING_START_TIME:
                if face_detection_process is None:
                    logging.info("Starting face detection.")
                    script = (
                        "/home/rash/.config/scripts/hyprland/presence_detection/"
                        "face_detector.py"
                    )
                    face_detection_process = subprocess.Popen([script])

            # --- Stage 2: Evaluate Face Detection Results ---
            if elapsed_time >= MONITORING_START_TIME:
                # Face detection initial window is complete, check results
                face_status = get_face_detection_status()
                logging.info(f"Face detection result: {face_status}")

                if face_status == "detected":
                    # Enter monitoring mode - keep idle_detection_status as "in_progress"
                    logging.info("Face detected. Entering monitoring mode.")

                    # Monitor both exit signal and face detection process
                    while True:
                        # Check for exit signal (user activity detected by hypridle)
                        if should_exit():
                            logging.info(
                                "Exit signal received during monitoring. Exiting gracefully."
                            )
                            break

                        # Check if face detection process is still running
                        if (
                            face_detection_process
                            and face_detection_process.poll() is not None
                        ):
                            # Face detection process has exited, check why
                            current_face_status = get_face_detection_status()
                            logging.info(
                                f"Face detection process exited. Status: {current_face_status}"
                            )

                            if current_face_status == "not_detected":
                                # Face detection stopped because no face was detected
                                logging.info(
                                    "Face detection stopped - no face detected. "
                                    "Setting status to inactive."
                                )
                                report_idle_detection_status("inactive")

                                # Wait for HA to process the change
                                time.sleep(3)

                                # Check if we should lock
                                if get_in_office_status() == "off":
                                    logging.info(
                                        "in_office is OFF. Proceeding to lock."
                                    )
                                    # Exit monitoring loop to go to locking stage
                                    break
                                else:
                                    logging.info(
                                        "in_office is ON. Continuing monitoring."
                                    )
                                    # Other sensors still detect presence, keep monitoring
                                    # But face detection has stopped, so we just wait
                                    # for exit signal
                                    while True:
                                        if should_exit():
                                            logging.info(
                                                "Exit signal received. Exiting gracefully."
                                            )
                                            return
                                        time.sleep(1)
                            else:
                                # Face detection process exited for some other reason, restart it
                                logging.info("Restarting face detection process.")
                                script = (
                                    "/home/rash/.config/scripts/hyprland/presence_detection/"
                                    "face_detector.py"
                                )
                                face_detection_process = subprocess.Popen([script])

                        time.sleep(1)

                    # If we get here and face status is not_detected, proceed to locking
                    if get_face_detection_status() == "not_detected":
                        break
                    else:
                        # User activity caused exit, normal exit
                        break
                else:
                    # No face detected - set status to inactive FIRST to break circular reference
                    logging.info(
                        "No face detected. Setting idle_detection_status to inactive."
                    )
                    report_idle_detection_status("inactive")

                    # Wait for HA to process the status change
                    time.sleep(3)

                    # Now proceed with locking evaluation
                    logging.info("Proceeding with locking evaluation.")
                    break

            time.sleep(1)

        # --- Stage 3: Handle No Face Detected Case ---
        # Only reach here if no face was detected (status already set to inactive)
        if get_face_detection_status() == "not_detected":
            # Check final in_office status for locking decision
            if get_in_office_status() == "off":
                logging.info("in_office is OFF. Locking session.")
                run_command(["loginctl", "lock-session"])

                # Wait 30 seconds then check again before DPMS off
                logging.info("Waiting 30 seconds before DPMS off...")
                for i in range(30):
                    if should_exit():
                        logging.info("Exit signal received during DPMS wait. Exiting.")
                        return
                    time.sleep(1)

                # Check in_office status again before DPMS (status might have changed)
                if get_in_office_status() == "off":
                    logging.info(
                        "in_office still OFF after 30s wait. Turning DPMS off."
                    )
                    run_command(["hyprctl", "dispatch", "dpms", "off"])
                else:
                    logging.info(
                        "in_office turned ON during wait. Not turning DPMS off."
                    )
            else:
                logging.info("in_office is ON. Not locking.")

    finally:
        # Always cleanup when exiting (user activity or natural exit)
        cleanup_flag_file()

        # Clean up exit flag if it exists
        try:
            FACE_PRESENCE_COORDINATOR_EXIT_FLAG.unlink()
        except FileNotFoundError:
            pass

        # Set idle detection status to inactive (if not already set)
        if IDLE_DETECTION_STATUS_FILE.exists():
            current_status = IDLE_DETECTION_STATUS_FILE.read_text().strip()
            if current_status != "inactive":
                report_idle_detection_status("inactive")
        logging.info("Face presence coordinator finished.")


if __name__ == "__main__":
    main()
