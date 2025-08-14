#!/home/rash/.config/scripts/hyprland/idle_management/.venv/bin/python

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

# Try to import face_recognition for person-specific recognition
try:
    import pickle

    import face_recognition

    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Import centralized configuration
from config import (
    LOGGING_CONFIG,
    get_detection_method_order,
    get_detection_method_param,
    get_detection_param,
    get_detection_timing_param,
    get_facial_recognition_param,
    get_fallback_setting,
    get_log_file,
    get_status_file,
    is_detection_method_enabled,
    is_facial_recognition_enabled,
)

# Fix Qt platform for Wayland/Hyprland compatibility - prevents crashes from cv2.destroyAllWindows()
import os
os.environ['QT_QPA_PLATFORM'] = 'xcb'


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
        min_area = get_detection_method_param("motion", "min_area") or 200

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


def load_reference_encodings():
    """Load reference face encodings for the target person."""
    if not is_facial_recognition_enabled() or not FACE_RECOGNITION_AVAILABLE:
        return []

    reference_dir = get_facial_recognition_param("reference_images_dir")
    supported_formats = get_facial_recognition_param("supported_image_formats")
    encodings_file = reference_dir / "encodings.pkl"

    # Try to load cached encodings first
    if encodings_file.exists():
        try:
            with open(encodings_file, "rb") as f:
                cached_data = pickle.load(f)
                logging.info(
                    f"Loaded {len(cached_data['encodings'])} cached face encodings"
                )
                return cached_data["encodings"]
        except Exception as e:
            logging.warning(f"Failed to load cached encodings: {e}")

    # If no cache, generate encodings from reference images
    # Note: For production use, encodings should be pre-generated during setup
    encodings = []
    reference_images = []

    for fmt in supported_formats:
        reference_images.extend(reference_dir.glob(f"*{fmt}"))

    if not reference_images:
        logging.warning(f"No reference images found in {reference_dir}")
        logging.warning("Run setup_facial_recognition.py to capture reference images")
        return []

    logging.info(f"Generating encodings from {len(reference_images)} reference images")
    logging.info(
        "Note: For better performance, use setup_facial_recognition.py to pre-generate encodings"
    )

    for image_path in reference_images:
        try:
            # Load image
            image = face_recognition.load_image_file(str(image_path))

            # Get face encodings
            face_encodings = face_recognition.face_encodings(
                image,
                model=get_facial_recognition_param("face_detection_model"),
                num_jitters=get_facial_recognition_param("num_jitters"),
            )

            if face_encodings:
                encodings.extend(face_encodings)
                logging.debug(
                    f"Generated {len(face_encodings)} encoding(s) from "
                    f"{image_path.name}"
                )
            else:
                logging.warning(f"No faces found in reference image: {image_path.name}")

        except Exception as e:
            logging.error(f"Error processing reference image {image_path.name}: {e}")

    if encodings:
        # Cache the encodings for future use
        try:
            with open(encodings_file, "wb") as f:
                pickle.dump({"encodings": encodings, "version": "1.0"}, f)
            logging.info(f"Cached {len(encodings)} face encodings to {encodings_file}")
        except Exception as e:
            logging.warning(f"Failed to cache encodings: {e}")

        logging.info(f"Successfully loaded {len(encodings)} reference face encodings")
    else:
        logging.error("No valid face encodings generated from reference images")
        logging.error(
            "Run setup_facial_recognition.py to capture proper reference images"
        )

    return encodings


def recognize_person(frame, known_encodings, tolerance=None):
    """Recognize if detected face belongs to the target person."""
    if not known_encodings or not FACE_RECOGNITION_AVAILABLE:
        return False, 0.0

    if tolerance is None:
        tolerance = get_facial_recognition_param("tolerance")

    try:
        # Find face locations
        face_locations = face_recognition.face_locations(
            frame, model=get_facial_recognition_param("face_locations_model")
        )

        if not face_locations:
            return False, 0.0

        # Get face encodings
        face_encodings = face_recognition.face_encodings(
            frame,
            face_locations,
            model=get_facial_recognition_param("face_detection_model"),
            num_jitters=get_facial_recognition_param("num_jitters"),
        )

        if not face_encodings:
            return False, 0.0

        # Compare each detected face against known encodings
        for face_encoding in face_encodings:
            # Get face distances (lower = better match)
            face_distances = face_recognition.face_distance(
                known_encodings, face_encoding
            )

            if len(face_distances) > 0:
                best_match_distance = np.min(face_distances)
                confidence = 1.0 - best_match_distance  # Convert distance to confidence

                # Check if any face matches within tolerance
                matches = face_recognition.compare_faces(
                    known_encodings, face_encoding, tolerance=tolerance
                )

                if any(matches):
                    logging.debug(
                        f"Person recognized! Confidence: {confidence:.3f}, "
                        f"Distance: {best_match_distance:.3f}"
                    )
                    return True, confidence

        return False, 0.0

    except Exception as e:
        logging.error(f"Error during facial recognition: {e}")
        return False, 0.0


def detect_human_presence(
    frame, previous_frame=None, face_mesh=None, known_encodings=None
):
    """Detect human presence using configurable detection method order."""

    # Get configured detection method order
    method_order = get_detection_method_order()
    fallback_enabled = get_fallback_setting("fallback_to_generic_detection")

    # If fallback is disabled, only try the highest-ranked enabled method
    if not fallback_enabled:
        for method in method_order:
            if _is_detection_method_available(
                method, face_mesh, known_encodings, previous_frame
            ):
                detected, result_method = _try_detection_method(
                    method, frame, previous_frame, face_mesh, known_encodings
                )
                if detected:
                    return True, result_method
                else:
                    # Method is available but didn't detect - stop here if no fallback
                    return False, "none"
        return False, "none"

    # If fallback is enabled, try methods in order until one succeeds
    for method in method_order:
        if _is_detection_method_available(
            method, face_mesh, known_encodings, previous_frame
        ):
            detected, result_method = _try_detection_method(
                method, frame, previous_frame, face_mesh, known_encodings
            )
            if detected:
                return True, result_method
            # Continue to next method if this one failed

    return False, "none"


def _is_detection_method_available(
    method, face_mesh=None, known_encodings=None, previous_frame=None
):
    """Check if a detection method is available/enabled."""
    # First check if the method is enabled in configuration
    if not is_detection_method_enabled(method):
        return False

    if method == "facial_recognition":
        return known_encodings and FACE_RECOGNITION_AVAILABLE
    elif method == "mediapipe_face":
        return face_mesh is not None
    elif method == "motion":
        return previous_frame is not None
    return False


def _try_detection_method(
    method, frame, previous_frame=None, face_mesh=None, known_encodings=None
):
    """Try a specific detection method and return (detected, method_name)."""
    try:
        if method == "facial_recognition":
            recognized, confidence = recognize_person(frame, known_encodings)
            if recognized:
                min_confidence = get_facial_recognition_param(
                    "min_recognition_confidence"
                )
                if confidence >= min_confidence:
                    logging.debug(
                        f"Target person recognized with confidence: {confidence:.3f}"
                    )
                    return True, "facial_recognition"
                else:
                    logging.debug(
                        f"Person detected but confidence too low: {confidence:.3f} < "
                        f"{min_confidence}"
                    )
                    return False, "facial_recognition"
            return False, "facial_recognition"

        elif method == "mediapipe_face":
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(frame_rgb)
            if results.multi_face_landmarks:
                logging.debug(
                    f"MediaPipe detected {len(results.multi_face_landmarks)} face(s)"
                )
                return True, "mediapipe_face"
            return False, "mediapipe_face"

        elif method == "motion":
            motion_detected = detect_motion(previous_frame, frame)
            if motion_detected:
                logging.debug("Motion detected")
                return True, "motion"
            return False, "motion"

    except Exception as e:
        logging.error(f"Error in detection method '{method}': {e}")
        return False, method

    return False, "unknown"


def run_detection(
    face_mesh=None,
    known_encodings=None,
    max_duration=None,
    initial_window=None,
    monitoring_mode=True,
):
    """Run human presence detection with optional continuous monitoring.

    Args:
        monitoring_mode: If True, enters monitoring mode after detection.
                        If False, just returns detection result.
    """
    if max_duration is None:
        max_duration = get_detection_timing_param("max_duration")
    if initial_window is None:
        initial_window = get_detection_timing_param("initial_window")

    # Report in_progress status at start (only in monitoring mode)
    if monitoring_mode:
        report_idle_status("in_progress")
    else:
        logging.info("Performing presence check with adaptive windows...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("Cannot open camera")
        if not monitoring_mode:
            # Just return failure result
            return False
        # Report failure and reset statuses (monitoring mode)
        report_face_status("not_detected")
        report_idle_status("inactive")
        return

    # Camera warm-up period - especially important for monitoring checks
    # Skip first few frames to allow camera to stabilize (exposure, focus, etc.)
    warmup_frames = (
        5 if not monitoring_mode else 10
    )  # More warmup for monitoring checks
    logging.debug(f"Camera warm-up: skipping first {warmup_frames} frames")
    for i in range(warmup_frames):
        ret, _ = cap.read()
        if not ret:
            logging.warning(f"Failed to read warm-up frame {i+1}/{warmup_frames}")
        time.sleep(0.1)  # Small delay between frames
    logging.debug("Camera warm-up completed")

    start_time = time.time()
    window_duration = initial_window
    frames_total = 0
    presence_detected_frames = 0
    detection_threshold = get_detection_param("threshold")
    previous_frame = None
    detection_methods = {
        "facial_recognition": 0,
        "mediapipe_face": 0,
        "motion": 0,
    }

    # Track frame detections with timestamps for recency weighting
    frame_detections = []  # List of (timestamp, detected_bool, method) tuples

    try:
        while time.time() - start_time < max_duration:
            # Check if user became active
            if check_user_active():
                logging.info("User became active, stopping human presence detection")
                if not monitoring_mode:
                    # Just return failure result
                    return False
                # Report status change (monitoring mode)
                report_face_status("not_detected")
                report_idle_status("inactive")
                return

            ret, frame = cap.read()
            if not ret:
                logging.error("Can't receive frame (stream end?). Exiting ...")
                break

            frames_total += 1

            # Detect human presence using facial recognition, MediaPipe and motion
            detected, method = detect_human_presence(
                frame,
                previous_frame,
                face_mesh,
                known_encodings,
            )

            if detected:
                presence_detected_frames += 1
                detection_methods[method] += 1
                logging.debug(f"Frame {frames_total}: Human detected via {method}")

            # Record detection with timestamp
            frame_timestamp = time.time()
            frame_detections.append(
                (frame_timestamp, detected, method if detected else None)
            )

            # Store frame for motion detection
            previous_frame = frame.copy()

            # Evaluate within the current window
            if time.time() - start_time >= window_duration:
                # Calculate recency-weighted detection rate
                current_time = time.time()
                recent_window_duration = get_detection_timing_param(
                    "recent_window_duration"
                )
                recent_threshold = get_detection_timing_param("recent_window_threshold")
                global_threshold = detection_threshold

                # Get recent frames (last N seconds)
                recent_frames = [
                    (ts, det, meth)
                    for ts, det, meth in frame_detections
                    if current_time - ts <= recent_window_duration
                ]

                # Calculate rates
                detection_rate = presence_detected_frames / frames_total
                recent_detected_count = sum(
                    1 for _, detected_bool, _ in recent_frames if detected_bool
                )
                recent_detection_rate = (
                    recent_detected_count / len(recent_frames) if recent_frames else 0
                )

                logging.info(
                    f"Window {window_duration}s: {presence_detected_frames}/{frames_total} "
                    f"frames ({detection_rate:.1%}) - Recent {recent_window_duration}s: "
                    f"{recent_detected_count}/{len(recent_frames)} "
                    f"({recent_detection_rate:.1%})"
                )
                logging.info(f"Detection methods used: {detection_methods}")

                # Prioritize recent detection
                presence_detected = False
                detection_reason = ""

                if recent_detection_rate >= recent_threshold:
                    presence_detected = True
                    detection_reason = (
                        f"recent window {recent_detection_rate:.1%} >= "
                        f"{recent_threshold:.1%}"
                    )
                    logging.info(f"Detection reason: {detection_reason}")
                elif detection_rate >= global_threshold:
                    presence_detected = True
                    detection_reason = (
                        f"overall window {detection_rate:.1%} >= {global_threshold:.1%}"
                    )
                else:
                    detection_reason = (
                        f"both recent {recent_detection_rate:.1%} < {recent_threshold:.1%} "
                        f"and overall {detection_rate:.1%} < {global_threshold:.1%}"
                    )

                logging.info(f"Detection decision: {detection_reason}")

                # Human presence detected if we exceed the threshold
                if presence_detected:
                    logging.info(
                        f"HUMAN PRESENCE DETECTED! Rate: {detection_rate:.1%} in {window_duration}s"
                    )
                    logging.info(f"Detection breakdown: {detection_methods}")

                    if not monitoring_mode:
                        # Just return the result without monitoring
                        cap.release()
                        cv2.destroyAllWindows()
                        return True

                    # Monitoring mode: report status and enter monitoring loop
                    report_face_status("detected")
                    # Keep idle_detection_status as in_progress as per requirements

                    # Release camera and start monitoring loop
                    cap.release()
                    cv2.destroyAllWindows()
                    logging.debug("Camera released, starting monitoring loop.")

                    # Monitor every minute until presence is no longer
                    # detected OR user becomes active
                    monitoring_start = time.time()
                    monitoring_interval = get_detection_timing_param(
                        "monitoring_interval"
                    )

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
                        if run_detection(
                            face_mesh, known_encodings, monitoring_mode=False
                        ):
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

        # Apply recency weighting to final decision
        current_time = time.time()
        recent_window_duration = get_detection_timing_param("recent_window_duration")
        recent_threshold = get_detection_timing_param("recent_window_threshold")

        # Get recent frames for final evaluation
        recent_frames = [
            (ts, det, meth)
            for ts, det, meth in frame_detections
            if current_time - ts <= recent_window_duration
        ]

        recent_detected_count = sum(
            1 for _, detected_bool, _ in recent_frames if detected_bool
        )
        final_recent_rate = (
            recent_detected_count / len(recent_frames) if recent_frames else 0
        )

        logging.info(
            f"Final: {presence_detected_frames}/{frames_total} frames "
            f"({final_detection_rate:.1%}) - Recent: {recent_detected_count}/"
            f"{len(recent_frames)} ({final_recent_rate:.1%}) over {max_duration}s"
        )

        # Determine final result with recency weighting
        final_presence_detected = False
        if final_recent_rate >= recent_threshold:
            final_presence_detected = True
            logging.info("Final: recent window priority - DETECTED")
        elif final_detection_rate >= detection_threshold:
            final_presence_detected = True
            logging.info("Final: overall window threshold - DETECTED")
        else:
            logging.info("Final: both thresholds failed - NOT DETECTED")

        if final_presence_detected:
            logging.info("FINAL RESULT: HUMAN PRESENCE DETECTED")

            if not monitoring_mode:
                # Just return the result without monitoring
                return True

            # Monitoring mode: report status and enter monitoring loop
            report_face_status("detected")
            # Keep idle_detection_status as in_progress

            # Release camera and start monitoring loop
            cap.release()
            cv2.destroyAllWindows()
            logging.debug("Camera released, starting monitoring loop.")

            # Monitor every minute until presence is no longer detected OR user becomes active
            monitoring_start = time.time()
            monitoring_interval = get_detection_timing_param("monitoring_interval")

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
                if run_detection(face_mesh, known_encodings, monitoring_mode=False):
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

            if not monitoring_mode:
                # Just return the result without reporting status
                return False

            # Monitoring mode: report status
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

    method_name = (
        "Facial Recognition + MediaPipe + Motion"
        if is_facial_recognition_enabled()
        else "MediaPipe + Motion"
    )
    logging.info(f"Starting optimized human presence detection ({method_name})")

    # Initialize facial recognition
    known_encodings = []
    if is_facial_recognition_enabled():
        if FACE_RECOGNITION_AVAILABLE:
            try:
                known_encodings = load_reference_encodings()
                if known_encodings:
                    logging.info(
                        f"Facial recognition enabled with {len(known_encodings)} "
                        "reference encodings"
                    )
                else:
                    logging.warning(
                        "Facial recognition enabled but no reference encodings loaded"
                    )
            except Exception as e:
                logging.error(f"Failed to load facial recognition encodings: {e}")
        else:
            logging.error(
                "Facial recognition enabled but face_recognition library not available"
            )
            logging.error("Install with: pip install face_recognition")

    # Initialize MediaPipe face mesh
    face_mesh = None
    if MEDIAPIPE_AVAILABLE and is_detection_method_enabled("mediapipe_face"):
        try:
            face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=get_detection_method_param(
                    "mediapipe_face", "min_detection_confidence"
                )
                or 0.5,
                min_tracking_confidence=get_detection_method_param(
                    "mediapipe_face", "min_tracking_confidence"
                )
                or 0.5,
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
        elif not is_detection_method_enabled("mediapipe_face"):
            logging.info("MediaPipe disabled in configuration")

    # Check if we have at least one detection method available
    if face_mesh is None and not known_encodings:
        logging.warning(
            "No MediaPipe or facial recognition available - "
            "only motion detection will be used"
        )
        logging.warning("Consider installing MediaPipe for better edge case detection")

    logging.info("Detection methods available:")
    logging.info(f"- Facial recognition: {'✓' if known_encodings else '✗'}")
    logging.info(f"- MediaPipe face detection: {'✓' if face_mesh else '✗'}")
    logging.info("- Motion detection: ✓")

    # Log detection configuration
    detection_order = get_detection_method_order()
    fallback_enabled = get_fallback_setting("fallback_to_generic_detection")
    logging.info(f"Detection method order: {' → '.join(detection_order)}")
    fallback_msg = (
        "Enabled (try all methods in order)"
        if fallback_enabled
        else "Disabled (only use highest-ranked available method)"
    )
    logging.info(f"Fallback behavior: {fallback_msg}")

    run_detection(face_mesh, known_encodings)


if __name__ == "__main__":
    main()
