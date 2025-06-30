#!/usr/bin/env python3

import argparse
import logging
import subprocess
import time
from pathlib import Path

import cv2


def setup_logging(debug=False):
    """Set up logging."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def report_status(status):
    """Report status to MQTT."""
    logging.info(f"Reporting status: {status}")
    status_file = Path("/tmp/mqtt/face_presence")
    status_file.parent.mkdir(parents=True, exist_ok=True)

    # Write status
    status_file.write_text(status)
    logging.debug(f"Status '{status}' written to {status_file}")


def quick_face_check(face_cascade, profile_cascade, duration=3):
    """Quick face detection check for monitoring."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Cannot open camera for monitoring check")
        return False

    start_time = time.time()
    frames_total = 0
    face_detected_frames = 0
    detection_threshold = 0.6

    try:
        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if not ret:
                logging.error("Can't receive frame during monitoring check")
                break

            frames_total += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_cascade.detectMultiScale(gray, 1.1, 3)
            profiles = profile_cascade.detectMultiScale(gray, 1.1, 3)

            if len(faces) > 0 or len(profiles) > 0:
                face_detected_frames += 1

        detection_rate = face_detected_frames / frames_total if frames_total > 0 else 0
        logging.debug(
            f"Monitoring check: {face_detected_frames}/{frames_total} frames ({detection_rate:.1%})"
        )

        return detection_rate >= detection_threshold

    finally:
        cap.release()
        cv2.destroyAllWindows()


def check_face_presence_coordinator_running():
    """Check if continuous face monitor should continue running (no exit flag)."""
    exit_flag = Path("/tmp/continuous_face_monitor_exit")
    return not exit_flag.exists()


def run_detection(face_cascade, profile_cascade, max_duration=10, initial_window=5):
    """Run face detection with continuous monitoring."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Cannot open camera")
        return

    start_time = time.time()
    window_duration = initial_window
    frames_total = 0
    face_detected_frames = 0

    # Require at least 60% of frames to have faces for more reliability
    detection_threshold = 0.6

    try:
        while time.time() - start_time < max_duration:
            ret, frame = cap.read()
            if not ret:
                logging.error("Can't receive frame (stream end?). Exiting ...")
                break

            frames_total += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Use more sensitive parameters for better detection
            faces = face_cascade.detectMultiScale(gray, 1.1, 3)
            profiles = profile_cascade.detectMultiScale(gray, 1.1, 3)

            has_face = len(faces) > 0 or len(profiles) > 0
            if has_face:
                face_detected_frames += 1

            # Evaluate within the current window
            if time.time() - start_time >= window_duration:
                detection_rate = face_detected_frames / frames_total
                logging.debug(
                    f"Window {window_duration}s: {face_detected_frames}/{frames_total} frames "
                    f"({detection_rate:.1%}) - threshold: {detection_threshold:.1%}"
                )

                # Face detected if we exceed the threshold
                if detection_rate >= detection_threshold:
                    logging.info(
                        f"FACE DETECTED! Rate: {detection_rate:.1%} in {window_duration}s"
                    )
                    report_status("detected")

                    # Release camera and start monitoring loop
                    cap.release()
                    cv2.destroyAllWindows()
                    logging.debug("Camera released, starting monitoring loop.")

                    # Monitor every minute until face is no longer detected OR idle manager stops
                    monitoring_start = time.time()
                    while True:
                        # Check if face presence coordinator is still running
                        # (user activity breaks this)
                        if not check_face_presence_coordinator_running():
                            logging.info(
                                "Face monitoring stopped (user activity detected). "
                                "Resetting status."
                            )
                            report_status("not_detected")
                            return

                        logging.info("Waiting 60 seconds before next face check...")

                        # Sleep in smaller chunks to check idle manager flag more frequently
                        for _ in range(60):
                            time.sleep(1)
                            if not check_face_presence_coordinator_running():
                                logging.info(
                                    "Face monitoring stopped during wait. "
                                    "Resetting status."
                                )
                                report_status("not_detected")
                                return

                        logging.info("Performing periodic face detection check...")
                        if quick_face_check(face_cascade, profile_cascade):
                            elapsed_monitoring = int(time.time() - monitoring_start)
                            logging.info(
                                f"Face still detected after {elapsed_monitoring}s of monitoring. "
                                "Continuing."
                            )
                        else:
                            logging.info(
                                "Face no longer detected. Reporting not_detected."
                            )
                            report_status("not_detected")
                            return
                    return

                # If we haven't reached max_duration, extend the window
                if window_duration < max_duration:
                    window_duration += 1
                    logging.debug(f"Extending detection window to {window_duration}s")
                else:
                    # Max duration reached, make final call
                    break

        # Final evaluation after loop finishes
        final_detection_rate = (
            face_detected_frames / frames_total if frames_total > 0 else 0
        )
        logging.info(
            f"Final evaluation: {face_detected_frames}/{frames_total} frames "
            f"({final_detection_rate:.1%}) over {max_duration}s"
        )

        if final_detection_rate >= detection_threshold:
            logging.info("FINAL RESULT: FACE DETECTED")
            report_status("detected")

            # Release camera and start monitoring loop
            cap.release()
            cv2.destroyAllWindows()
            logging.debug("Camera released, starting monitoring loop.")

            # Monitor every minute until face is no longer detected OR idle manager stops
            monitoring_start = time.time()
            while True:
                # Check if face presence coordinator is still running (user activity breaks this)
                if not check_face_presence_coordinator_running():
                    logging.info(
                        "Face monitoring stopped (user activity detected). "
                        "Resetting status."
                    )
                    report_status("not_detected")
                    return

                logging.info("Waiting 60 seconds before next face check...")

                # Sleep in smaller chunks to check idle manager flag more frequently
                for _ in range(60):
                    time.sleep(1)
                    if not check_face_presence_coordinator_running():
                        logging.info(
                            "Face monitoring stopped during wait. Resetting status."
                        )
                        report_status("not_detected")
                        return

                logging.info("Performing periodic face detection check...")
                if quick_face_check(face_cascade, profile_cascade):
                    elapsed_monitoring = int(time.time() - monitoring_start)
                    logging.info(
                        f"Face still detected after {elapsed_monitoring}s of monitoring. "
                        "Continuing."
                    )
                else:
                    logging.info("Face no longer detected. Reporting not_detected.")
                    report_status("not_detected")
                    return
        else:
            logging.info("FINAL RESULT: NO FACE DETECTED")
            report_status("not_detected")

    finally:
        # Only release if not already released
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        logging.debug("Camera released and windows closed.")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Face detection script for idle management."
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()
    setup_logging(args.debug)

    # Paths to cascade files
    # These paths may need to be adjusted depending on the system setup
    base_path = Path("/usr/share/opencv4/haarcascades/")
    face_cascade_path = base_path / "haarcascade_frontalface_default.xml"
    profile_cascade_path = base_path / "haarcascade_profileface.xml"

    if not face_cascade_path.exists() or not profile_cascade_path.exists():
        logging.error("Haar cascade files not found. Please check the paths.")
        logging.error(f"Looked for: {face_cascade_path}")
        logging.error(f"Looked for: {profile_cascade_path}")
        # Attempt to find the files
        try:
            logging.info("Attempting to find cascade files using `find`...")
            result = subprocess.run(
                ["find", "/usr", "-name", "haarcascade_frontalface_default.xml"],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                found_path = Path(result.stdout.strip()).parent
                logging.info(
                    f"Found a possible location for cascade files: {found_path}"
                )
                logging.info("Please update the `base_path` in this script.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.error(f"Error while trying to find cascade files: {e}")
        return

    face_cascade = cv2.CascadeClassifier(str(face_cascade_path))
    profile_cascade = cv2.CascadeClassifier(str(profile_cascade_path))

    run_detection(face_cascade, profile_cascade)


if __name__ == "__main__":
    main()
