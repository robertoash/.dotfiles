#!/home/rash/.config/scripts/hyprland/idle_management/.direnv/python-3.12/bin/python

import argparse
import logging
import time

import cv2
import numpy as np

# Try to import MediaPipe for enhanced detection
try:
    import mediapipe as mp

    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

# Import centralized configuration
from config import (
    FACE_DETECTION,
    LOGGING_CONFIG,
    get_detection_param,
    get_log_file,
    get_status_file,
)


def setup_logging(debug=False):
    """Set up logging."""
    log_level = logging.DEBUG if debug else logging.INFO
    log_file = get_log_file("face_detector")

    logging.basicConfig(
        level=log_level,
        format=LOGGING_CONFIG["format"],
        datefmt=LOGGING_CONFIG["date_format"],
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )


def report_face_status(status):
    """Report human presence status to MQTT."""
    logging.info(f"Reporting human presence: {status}")
    status_file = get_status_file("face_presence")
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(status)
    logging.debug(f"Human presence '{status}' written to {status_file}")


def report_idle_status(status):
    """Report idle detection status to MQTT."""
    logging.info(f"Reporting idle detection: {status}")
    status_file = get_status_file("idle_detection_status")
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(status)
    logging.debug(f"Idle detection '{status}' written to {status_file}")


def check_user_active():
    """Check if user has become active by monitoring linux_mini_status."""
    try:
        status_file = get_status_file("linux_mini_status")
        if status_file.exists():
            content = status_file.read_text().strip()
            return content == "active"
        return False
    except Exception as e:
        logging.warning(f"Error checking user status: {e}")
        return False


def detect_motion(frame1, frame2, min_area=None):
    """Detect motion between two frames."""
    if min_area is None:
        min_area = get_detection_param("motion_min_area")

    # Convert frames to grayscale
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

    # Calculate absolute difference
    diff = cv2.absdiff(gray1, gray2)

    # Apply threshold
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    # Apply morphological operations to reduce noise
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Check if any contour is large enough
    for contour in contours:
        if cv2.contourArea(contour) > min_area:
            return True

    return False


def detect_human_presence(frame, previous_frame=None, face_mesh=None):
    """Detect human presence using MediaPipe and motion detection."""

    # MediaPipe face detection (excellent for all angles and edge cases)
    if face_mesh is not None:
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)
        if results.multi_face_landmarks:
            logging.debug(
                f"MediaPipe detected {len(results.multi_face_landmarks)} face(s)"
            )
            return True, "mediapipe_face"

    # Motion detection (catches subtle movements and interactions)
    if previous_frame is not None:
        motion_detected = detect_motion(previous_frame, frame)
        if motion_detected:
            logging.debug("Motion detected")
            return True, "motion"

    return False, "none"


def quick_presence_check(face_mesh=None, duration=None):
    """Quick human presence detection check for monitoring."""
    if duration is None:
        duration = FACE_DETECTION["quick_check_duration"]

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Cannot open camera for monitoring check")
        return False

    start_time = time.time()
    frames_total = 0
    presence_detected_frames = 0
    detection_threshold = get_detection_param("threshold")
    previous_frame = None

    try:
        while time.time() - start_time < duration:
            # Check if user became active during quick check
            if check_user_active():
                logging.info("User became active during quick presence check, stopping")
                return False

            ret, frame = cap.read()
            if not ret:
                logging.error("Can't receive frame during monitoring check")
                break

            frames_total += 1

            # Detect human presence using MediaPipe and motion
            detected, method = detect_human_presence(
                frame,
                previous_frame,
                face_mesh,
            )

            if detected:
                presence_detected_frames += 1
                logging.debug(f"Frame {frames_total}: Human detected via {method}")

            # Store frame for motion detection
            previous_frame = frame.copy()

        detection_rate = (
            presence_detected_frames / frames_total if frames_total > 0 else 0
        )
        logging.debug(
            f"Monitoring check: {presence_detected_frames}/{frames_total} "
            f"frames ({detection_rate:.1%})"
        )

        return detection_rate >= detection_threshold

    finally:
        cap.release()
        cv2.destroyAllWindows()


def run_detection(face_mesh=None, max_duration=None, initial_window=None):
    """Run human presence detection with continuous monitoring."""
    if max_duration is None:
        max_duration = FACE_DETECTION["max_duration"]
    if initial_window is None:
        initial_window = FACE_DETECTION["initial_window"]

    # Report in_progress status at start
    report_idle_status("in_progress")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Cannot open camera")
        # Report failure and reset statuses
        report_face_status("not_detected")
        report_idle_status("inactive")
        return

    start_time = time.time()
    window_duration = initial_window
    frames_total = 0
    presence_detected_frames = 0
    detection_threshold = get_detection_param("threshold")
    previous_frame = None
    detection_methods = {
        "mediapipe_face": 0,
        "motion": 0,
    }

    try:
        while time.time() - start_time < max_duration:
            # Check if user became active
            if check_user_active():
                logging.info("User became active, stopping human presence detection")
                report_face_status("not_detected")
                report_idle_status("inactive")
                return

            ret, frame = cap.read()
            if not ret:
                logging.error("Can't receive frame (stream end?). Exiting ...")
                break

            frames_total += 1

            # Detect human presence using MediaPipe and motion
            detected, method = detect_human_presence(
                frame,
                previous_frame,
                face_mesh,
            )

            if detected:
                presence_detected_frames += 1
                detection_methods[method] += 1
                logging.debug(f"Frame {frames_total}: Human detected via {method}")

            # Store frame for motion detection
            previous_frame = frame.copy()

            # Evaluate within the current window
            if time.time() - start_time >= window_duration:
                detection_rate = presence_detected_frames / frames_total
                logging.info(
                    f"Window {window_duration}s: {presence_detected_frames}/{frames_total} frames "
                    f"({detection_rate:.1%}) - threshold: {detection_threshold:.1%}"
                )
                logging.info(f"Detection methods used: {detection_methods}")

                # Human presence detected if we exceed the threshold
                if detection_rate >= detection_threshold:
                    logging.info(
                        f"HUMAN PRESENCE DETECTED! Rate: {detection_rate:.1%} in {window_duration}s"
                    )
                    logging.info(f"Detection breakdown: {detection_methods}")
                    report_face_status("detected")
                    # Keep idle_detection_status as in_progress as per requirements

                    # Release camera and start monitoring loop
                    cap.release()
                    cv2.destroyAllWindows()
                    logging.debug("Camera released, starting monitoring loop.")

                    # Monitor every minute until presence is no longer
                    # detected OR user becomes active
                    monitoring_start = time.time()
                    monitoring_interval = FACE_DETECTION["monitoring_interval"]

                    while True:
                        # Check if user became active
                        if check_user_active():
                            logging.info(
                                "User became active during monitoring, stopping presence detection"
                            )
                            report_face_status("not_detected")
                            report_idle_status("inactive")
                            return

                        logging.info(
                            f"Waiting {monitoring_interval} seconds before next presence check..."
                        )

                        # Sleep in smaller chunks to check user activity more frequently
                        for _ in range(monitoring_interval):
                            time.sleep(1)
                            if check_user_active():
                                logging.info(
                                    "User became active during wait, stopping presence detection"
                                )
                                report_face_status("not_detected")
                                report_idle_status("inactive")
                                return

                        logging.info("Performing periodic human presence check...")
                        if quick_presence_check(face_mesh):
                            elapsed_monitoring = int(time.time() - monitoring_start)
                            logging.info(
                                f"Human presence still detected after {elapsed_monitoring}s "
                                "of monitoring. "
                                "Continuing."
                            )
                        else:
                            logging.info(
                                "Human presence no longer detected. Reporting not_detected."
                            )
                            report_face_status("not_detected")
                            report_idle_status("inactive")
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
            presence_detected_frames / frames_total if frames_total > 0 else 0
        )
        logging.info(
            f"Final evaluation: {presence_detected_frames}/{frames_total} frames "
            f"({final_detection_rate:.1%}) over {max_duration}s"
        )
        logging.info(f"Final detection breakdown: {detection_methods}")

        if final_detection_rate >= detection_threshold:
            logging.info("FINAL RESULT: HUMAN PRESENCE DETECTED")
            report_face_status("detected")
            # Keep idle_detection_status as in_progress

            # Release camera and start monitoring loop
            cap.release()
            cv2.destroyAllWindows()
            logging.debug("Camera released, starting monitoring loop.")

            # Monitor every minute until presence is no longer detected OR user becomes active
            monitoring_start = time.time()
            monitoring_interval = FACE_DETECTION["monitoring_interval"]

            while True:
                # Check if user became active
                if check_user_active():
                    logging.info(
                        "User became active during monitoring, stopping presence detection"
                    )
                    report_face_status("not_detected")
                    report_idle_status("inactive")
                    return

                logging.info(
                    f"Waiting {monitoring_interval} seconds before next presence check..."
                )

                # Sleep in smaller chunks to check user activity more frequently
                for _ in range(monitoring_interval):
                    time.sleep(1)
                    if check_user_active():
                        logging.info(
                            "User became active during wait, stopping presence detection"
                        )
                        report_face_status("not_detected")
                        report_idle_status("inactive")
                        return

                logging.info("Performing periodic human presence check...")
                if quick_presence_check(face_mesh):
                    elapsed_monitoring = int(time.time() - monitoring_start)
                    logging.info(
                        f"Human presence still detected after {elapsed_monitoring}s of monitoring. "
                        "Continuing."
                    )
                else:
                    logging.info(
                        "Human presence no longer detected. Reporting not_detected."
                    )
                    report_face_status("not_detected")
                    report_idle_status("inactive")
                    return
        else:
            logging.info("FINAL RESULT: NO HUMAN PRESENCE DETECTED")
            report_face_status("not_detected")
            report_idle_status("inactive")

    finally:
        # Only release if not already released
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        logging.debug("Camera released and windows closed.")

        # Clean up MediaPipe resources
        if face_mesh is not None:
            try:
                face_mesh.close()
            except Exception as e:
                logging.debug(f"Error closing MediaPipe face mesh: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Simplified human presence detection using MediaPipe + Motion."
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()
    setup_logging(args.debug)

    logging.info("Starting optimized human presence detection (MediaPipe + Motion)")

    # Initialize MediaPipe face mesh
    face_mesh = None
    if MEDIAPIPE_AVAILABLE and get_detection_param("mediapipe_enabled"):
        try:
            face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=get_detection_param(
                    "mediapipe_min_detection_confidence"
                ),
                min_tracking_confidence=get_detection_param(
                    "mediapipe_min_tracking_confidence"
                ),
            )
            logging.info("MediaPipe face detection enabled (excellent for all angles)")
        except Exception as e:
            logging.warning(f"Failed to initialize MediaPipe: {e}")
            face_mesh = None
    else:
        if not MEDIAPIPE_AVAILABLE:
            logging.warning(
                "MediaPipe not available (install with: pip install mediapipe)"
            )
        elif not get_detection_param("mediapipe_enabled"):
            logging.info("MediaPipe disabled in configuration")

    # Check if we have at least one detection method available
    if face_mesh is None:
        logging.warning("No MediaPipe available - only motion detection will be used")
        logging.warning("Consider installing MediaPipe for better edge case detection")

    logging.info("Detection methods available:")
    logging.info(f"- MediaPipe face detection: {'✓' if face_mesh else '✗'}")
    logging.info("- Motion detection: ✓")

    run_detection(face_mesh)


if __name__ == "__main__":
    main()
