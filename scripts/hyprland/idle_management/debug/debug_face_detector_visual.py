#!/home/rash/.config/scripts/hyprland/idle_management/.direnv/python-3.12/bin/python

import argparse
import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Fix Qt platform for Wayland/Hyprland compatibility - must be before OpenCV GUI
os.environ['QT_QPA_PLATFORM'] = 'xcb'

# Try to import MediaPipe for enhanced detection
try:
    import mediapipe as mp

    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

# Try to import face_recognition for person-specific recognition
try:
    import face_recognition

    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import centralized configuration
from config import (  # noqa: E402
    get_detection_method_param,
    get_detection_param,
    get_detection_timing_param,
    get_facial_recognition_param,
    is_detection_method_enabled,
    is_facial_recognition_enabled,
)


class VisualFaceDetector:
    """Visual debugging tool for optimized face detection system."""

    def __init__(self):
        self.face_mesh = None
        self.previous_frame = None
        self.known_encodings = []

        # Detection statistics
        self.frame_count = 0
        self.detection_stats = {
            "facial_recognition": 0,
            "mediapipe_face": 0,
            "motion": 0,
            "total_detections": 0,
        }

        # Facial recognition confidence tracking
        self.recognition_confidences = []  # List of confidence scores
        self.max_confidence_history = 20  # Keep last 20 confidence scores

        # Rolling window for last 5 seconds detection rate
        self.detection_events = []  # List of (timestamp, detected_bool) tuples
        self.rolling_window_seconds = 5

        # Frame-level detection tracking for recency weighting
        self.frame_detections = (
            []
        )  # List of (timestamp, detected_bool) tuples for frame-level analysis

        # Performance optimization settings
        self.frame_skip = 2  # Process every Nth frame for better performance
        self.processed_frame_count = 0  # Count of actually processed frames
        self.last_detection_method = None  # Track what method worked last

        # Colors for different detection types
        self.colors = {
            "facial_recognition": (0, 255, 0),  # Green - target person recognized!
            "mediapipe_face": (0, 128, 255),  # Orange - excellent for all angles!
            "motion": (255, 0, 255),  # Magenta
            "unknown_person": (0, 0, 255),  # Red - face detected but not recognized
            "text": (255, 255, 255),  # White
            "background": (0, 0, 0),  # Black
        }

    def load_detection_methods(self):
        """Load detection methods."""
        print("Loading detection methods...")

        # Initialize facial recognition
        if is_facial_recognition_enabled():
            if FACE_RECOGNITION_AVAILABLE:
                try:
                    # Import from face_detector module
                    from face_detector import load_reference_encodings

                    all_encodings = load_reference_encodings()
                    if all_encodings:
                        # PERFORMANCE OPTIMIZATION: Limit encodings for debug tool
                        max_encodings_for_debug = 10
                        if len(all_encodings) > max_encodings_for_debug:
                            print(
                                f"⚠️ Performance optimization: Using first "
                                f"{max_encodings_for_debug} of {len(all_encodings)} "
                                f"reference encodings for debug"
                            )
                            print(
                                f"   (Production face_detector.py will use all "
                                f"{len(all_encodings)} encodings)"
                            )
                            self.known_encodings = all_encodings[
                                :max_encodings_for_debug
                            ]
                        else:
                            self.known_encodings = all_encodings

                        print(
                            f"✓ Facial recognition enabled with "
                            f"{len(self.known_encodings)} reference encodings (debug mode)"
                        )

                    else:
                        print(
                            "⚠ Facial recognition enabled but no reference encodings loaded"
                        )
                except Exception as e:
                    print(f"⚠ Failed to load facial recognition: {e}")
                    self.known_encodings = []
            else:
                print(
                    "⚠ Facial recognition enabled but face_recognition library not available"
                )
                print("  Install with: pip install face_recognition")
        else:
            print("⚠ Facial recognition disabled in configuration")

        # Initialize MediaPipe face mesh
        if MEDIAPIPE_AVAILABLE and is_detection_method_enabled("mediapipe_face"):
            try:
                self.face_mesh = mp.solutions.face_mesh.FaceMesh(
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
                print("✓ MediaPipe face detection enabled (excellent for all angles)")
            except Exception as e:
                print(f"⚠ Failed to initialize MediaPipe: {e}")
                self.face_mesh = None
        else:
            if not MEDIAPIPE_AVAILABLE:
                print("⚠ MediaPipe not available (install with: pip install mediapipe)")
            elif not is_detection_method_enabled("mediapipe_face"):
                print("⚠ MediaPipe disabled in configuration")

        print("✓ Motion detection: enabled")

        print(
            f"✓ Facial recognition: {'enabled' if self.known_encodings else 'disabled'}"
        )
        print(
            f"✓ MediaPipe face detection: {'enabled' if self.face_mesh else 'disabled'}"
        )

        # Performance warning
        if len(self.known_encodings) > 15:
            print(
                f"⚠️ Performance Warning: {len(self.known_encodings)} reference encodings detected"
            )
            print(
                "   Consider using setup_facial_recognition.py --regenerate to clean up bad images"
            )
            print("   Optimal range: 5-10 high-quality reference images")

        return True

    def detect_motion(self, frame1, frame2, debug_display=None):
        """Detect motion between two frames with optional debug display."""
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
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Check if any contour is large enough and draw them if debug display provided
        motion_detected = False
        if debug_display is not None:
            # Show motion threshold image in corner
            small_thresh = cv2.resize(thresh, (160, 120))
            debug_display[10:130, 10:170] = cv2.cvtColor(
                small_thresh, cv2.COLOR_GRAY2BGR
            )
            cv2.rectangle(debug_display, (8, 8), (172, 132), self.colors["motion"], 2)
            cv2.putText(
                debug_display,
                "Motion Thresh",
                (12, 145),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                self.colors["motion"],
                1,
            )

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                motion_detected = True
                if debug_display is not None:
                    # Draw motion contours
                    cv2.drawContours(
                        debug_display, [contour], -1, self.colors["motion"], 2
                    )
                    # Draw bounding box
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(
                        debug_display, (x, y), (x + w, y + h), self.colors["motion"], 2
                    )
                    cv2.putText(
                        debug_display,
                        f"Motion {int(area)}",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        self.colors["motion"],
                        2,
                    )

        return motion_detected

    def recognize_person_visual(self, frame):
        """Recognize if detected face belongs to the target person with visual feedback."""
        if not self.known_encodings or not FACE_RECOGNITION_AVAILABLE:
            return False, 0.0, None

        tolerance = get_facial_recognition_param("tolerance")
        min_confidence = get_facial_recognition_param("min_recognition_confidence")

        try:
            # Find face locations
            face_locations = face_recognition.face_locations(
                frame, model=get_facial_recognition_param("face_locations_model")
            )

            if not face_locations:
                return False, 0.0, None

            # Get face encodings
            face_encodings = face_recognition.face_encodings(
                frame,
                face_locations,
                model=get_facial_recognition_param("face_detection_model"),
                num_jitters=get_facial_recognition_param("num_jitters"),
            )

            if not face_encodings:
                return False, 0.0, face_locations

            # Compare each detected face against known encodings
            best_confidence = 0.0
            recognized = False

            for (top, right, bottom, left), face_encoding in zip(
                face_locations, face_encodings
            ):
                # Get face distances (lower = better match)
                face_distances = face_recognition.face_distance(
                    self.known_encodings, face_encoding
                )

                if len(face_distances) > 0:
                    best_match_distance = np.min(face_distances)
                    confidence = 1.0 - best_match_distance

                    # Update best confidence
                    if confidence > best_confidence:
                        best_confidence = confidence

                    # Check if any face matches within tolerance
                    matches = face_recognition.compare_faces(
                        self.known_encodings, face_encoding, tolerance=tolerance
                    )

                    if any(matches) and confidence >= min_confidence:
                        recognized = True

            return recognized, best_confidence, face_locations

        except Exception as e:
            print(f"Error during facial recognition: {e}")
            return False, 0.0, None

    def update_rolling_detection_rate(self, current_time, any_detected):
        """Update rolling detection rate for the last 5 seconds."""
        # Add current detection event
        self.detection_events.append((current_time, any_detected))

        # Remove events older than rolling window
        cutoff_time = current_time - self.rolling_window_seconds
        self.detection_events = [
            (timestamp, detected)
            for timestamp, detected in self.detection_events
            if timestamp >= cutoff_time
        ]

    def get_rolling_detection_rate(self):
        """Calculate detection rate for the rolling window."""
        if not self.detection_events:
            return 0.0

        detected_count = sum(1 for _, detected in self.detection_events if detected)
        return detected_count / len(self.detection_events)

    def update_frame_detections(self, current_time, detected):
        """Track frame-level detection events for recency weighting."""
        self.frame_detections.append((current_time, detected))

    def evaluate_recency_weighting(self, current_time):
        """
        Evaluate detection using recency weighting logic.

        Returns:
            tuple: (overall_rate, recent_rate, detection_decision, decision_reason)
        """
        # Get recency weighting configuration
        recent_window_duration = (
            get_detection_timing_param("recent_window_duration") or 3
        )
        recent_window_threshold = (
            get_detection_timing_param("recent_window_threshold") or 0.7
        )
        overall_threshold = get_detection_param("threshold") or 0.5

        if not self.frame_detections:
            return 0.0, 0.0, False, "No frame data"

        # Calculate overall detection rate
        overall_detected = sum(1 for _, detected in self.frame_detections if detected)
        overall_rate = overall_detected / len(self.frame_detections)

        # Calculate recent window detection rate
        recent_cutoff = current_time - recent_window_duration
        recent_frames = [
            (timestamp, detected)
            for timestamp, detected in self.frame_detections
            if timestamp >= recent_cutoff
        ]

        if recent_frames:
            recent_detected = sum(1 for _, detected in recent_frames if detected)
            recent_rate = recent_detected / len(recent_frames)
        else:
            recent_rate = 0.0

        # Apply recency weighting decision logic
        if recent_rate >= recent_window_threshold:
            return (
                overall_rate,
                recent_rate,
                True,
                f"recent window {recent_rate:.1%} >= {recent_window_threshold:.1%}",
            )
        elif overall_rate >= overall_threshold:
            return (
                overall_rate,
                recent_rate,
                True,
                f"overall window {overall_rate:.1%} >= {overall_threshold:.1%}",
            )
        else:
            return overall_rate, recent_rate, False, "both rates below thresholds"

    def clear_old_frame_detections(self, current_time, max_window_duration=10):
        """Remove old frame detection data beyond the maximum window."""
        cutoff_time = current_time - max_window_duration
        self.frame_detections = [
            (timestamp, detected)
            for timestamp, detected in self.frame_detections
            if timestamp >= cutoff_time
        ]

    def detect_all_methods(self, frame):
        """Detect using facial recognition, MediaPipe and motion
        and return results with visual annotations."""
        results = {}
        annotated_frame = frame.copy()
        recognition_confidence = 0.0

        # PERFORMANCE OPTIMIZATION: Frame skipping for real-time display
        self.frame_count += 1
        # ✅ FIX: Always process first frame, then skip according to frame_skip
        should_process = (self.frame_count == 1) or (
            (self.frame_count - 1) % self.frame_skip == 0
        )

        if should_process:
            self.processed_frame_count += 1

        # Facial recognition (person-specific detection)
        results["facial_recognition"] = False
        face_locations_from_recognition = None

        if (
            should_process
            and self.known_encodings
            and FACE_RECOGNITION_AVAILABLE
            and is_facial_recognition_enabled()
        ):
            recognized, confidence, face_locations = self.recognize_person_visual(frame)
            results["facial_recognition"] = recognized
            recognition_confidence = confidence
            face_locations_from_recognition = face_locations

            # Track confidence history
            if confidence > 0:
                self.recognition_confidences.append(confidence)
                if len(self.recognition_confidences) > self.max_confidence_history:
                    self.recognition_confidences.pop(0)

            # Draw facial recognition results
            if face_locations:
                for top, right, bottom, left in face_locations:
                    if recognized:
                        # Green box for recognized person
                        color = self.colors["facial_recognition"]
                        label = f"RECOGNIZED ({confidence:.2f})"
                        thickness = 4
                        self.last_detection_method = "facial_recognition"
                    else:
                        # Red box for unknown person
                        color = self.colors["unknown_person"]
                        label = f"UNKNOWN ({confidence:.2f})"
                        thickness = 3

                    cv2.rectangle(
                        annotated_frame,
                        (left, top),
                        (right, bottom),
                        color,
                        thickness,
                    )
                    cv2.putText(
                        annotated_frame,
                        label,
                        (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2,
                    )

        # Fallback detection methods (if facial recognition disabled or fallback enabled)
        # ✅ PERFORMANCE FIX: Skip fallback methods if facial recognition already succeeded
        skip_fallback = (
            results["facial_recognition"] and is_facial_recognition_enabled()
        )

        # MediaPipe face detection (best for all angles and edge cases)
        results["mediapipe_face"] = False
        if should_process and self.face_mesh is not None and not skip_fallback:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_results = self.face_mesh.process(frame_rgb)
            if mp_results.multi_face_landmarks:
                results["mediapipe_face"] = True
                self.last_detection_method = "mediapipe_face"
                # Only draw MediaPipe landmarks if facial recognition didn't find faces
                if not face_locations_from_recognition:
                    # Draw face mesh landmarks for first detected face
                    landmarks = mp_results.multi_face_landmarks[0]
                    # Draw key landmarks for visual feedback
                    h, w = frame.shape[:2]
                    key_points = [
                        10,
                        151,
                        9,
                        175,
                        197,
                        196,
                    ]  # Forehead, nose, chin, cheeks
                    for point_idx in key_points:
                        if point_idx < len(landmarks.landmark):
                            landmark = landmarks.landmark[point_idx]
                            x = int(landmark.x * w)
                            y = int(landmark.y * h)
                            cv2.circle(
                                annotated_frame,
                                (x, y),
                                3,
                                self.colors["mediapipe_face"],
                                -1,
                            )

                    # Draw bounding box around face
                    xs = [int(landmark.x * w) for landmark in landmarks.landmark]
                    ys = [int(landmark.y * h) for landmark in landmarks.landmark]
                    x_min, x_max = min(xs), max(xs)
                    y_min, y_max = min(ys), max(ys)
                    cv2.rectangle(
                        annotated_frame,
                        (x_min - 10, y_min - 10),
                        (x_max + 10, y_max + 10),
                        self.colors["mediapipe_face"],
                        2,
                    )
                    cv2.putText(
                        annotated_frame,
                        "MediaPipe Face",
                        (x_min - 10, y_min - 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        self.colors["mediapipe_face"],
                        2,
                    )

        # Motion detection (only if no face detection succeeded)
        results["motion"] = False
        if (
            should_process
            and self.previous_frame is not None
            and not (results["facial_recognition"] or results["mediapipe_face"])
        ):
            results["motion"] = self.detect_motion(
                self.previous_frame, frame, annotated_frame
            )
            if results["motion"]:
                self.last_detection_method = "motion"

        # Store additional info for status display
        results["_recognition_confidence"] = recognition_confidence
        results["_should_process"] = should_process
        results["_processed_frame_count"] = self.processed_frame_count

        return results, annotated_frame

    def draw_status_overlay(
        self,
        frame,
        results,
        detection_rate,
        elapsed_time,
        rolling_rate,
        overall_rate=None,
        recent_rate=None,
        recency_decision=None,
        decision_reason=None,
    ):
        """Draw status information overlay on the frame."""
        height, width = frame.shape[:2]

        # Semi-transparent overlay for status
        overlay = frame.copy()
        cv2.rectangle(
            overlay, (width - 350, 0), (width, 250), self.colors["background"], -1
        )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        y_offset = 25
        line_height = 22

        # Title
        title = "Enhanced Presence Detection"
        if is_facial_recognition_enabled() and self.known_encodings:
            title = "Facial Recognition + Detection"

        cv2.putText(
            frame,
            title,
            (width - 345, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.colors["text"],
            2,
        )
        y_offset += line_height + 8

        # Detection status for each method
        methods = []

        # Add facial recognition if enabled
        if is_facial_recognition_enabled() and self.known_encodings:
            methods.append(("Facial Recognition", "facial_recognition"))

        methods.extend(
            [
                ("MediaPipe Face", "mediapipe_face"),
                ("Motion", "motion"),
            ]
        )

        for method_name, method_key in methods:
            if method_key == "mediapipe_face" and self.face_mesh is None:
                status = "DISABLED"
                color = (128, 128, 128)  # Gray
            elif method_key == "facial_recognition" and not self.known_encodings:
                status = "DISABLED"
                color = (128, 128, 128)  # Gray
            else:
                status = (
                    "DETECTED" if results.get(method_key, False) else "NOT DETECTED"
                )
                if method_key == "facial_recognition" and results.get(
                    method_key, False
                ):
                    color = self.colors[
                        "facial_recognition"
                    ]  # Green for recognized person
                elif (
                    method_key == "facial_recognition"
                    and "_recognition_confidence" in results
                    and results["_recognition_confidence"] > 0
                ):
                    color = self.colors["unknown_person"]  # Red for unknown person
                    status = "UNKNOWN PERSON"
                else:
                    color = (
                        self.colors.get(method_key, (128, 128, 128))
                        if results.get(method_key, False)
                        else (128, 128, 128)
                    )

            cv2.putText(
                frame,
                f"{method_name}:",
                (width - 340, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                self.colors["text"],
                1,
            )
            cv2.putText(
                frame,
                status,
                (width - 180, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
            )
            y_offset += line_height

        # Facial recognition confidence info
        if is_facial_recognition_enabled() and self.known_encodings:
            y_offset += 5
            current_confidence = results.get("_recognition_confidence", 0.0)
            avg_confidence = (
                sum(self.recognition_confidences) / len(self.recognition_confidences)
                if self.recognition_confidences
                else 0.0
            )

            cv2.putText(
                frame,
                "Recognition Confidence:",
                (width - 340, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                self.colors["text"],
                1,
            )
            y_offset += line_height

            cv2.putText(
                frame,
                f"  Current: {current_confidence:.3f}",
                (width - 335, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                self.colors["text"],
                1,
            )
            y_offset += line_height - 3

            cv2.putText(
                frame,
                f"  Average: {avg_confidence:.3f}",
                (width - 335, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                self.colors["text"],
                1,
            )
            y_offset += line_height - 3

            threshold = get_facial_recognition_param("min_recognition_confidence")
            cv2.putText(
                frame,
                f"  Threshold: {threshold:.3f}",
                (width - 335, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                self.colors["text"],
                1,
            )
            y_offset += line_height + 5

        # Overall detection status
        threshold = get_detection_param("threshold")
        any_detected = any(
            v
            for k, v in results.items()
            if not k.startswith("_") and isinstance(v, bool)
        )
        overall_status = "PRESENT" if any_detected else "NOT PRESENT"
        overall_color = (0, 255, 0) if any_detected else (0, 0, 255)

        cv2.putText(
            frame,
            "Overall Status:",
            (width - 340, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            self.colors["text"],
            2,
        )
        cv2.putText(
            frame,
            overall_status,
            (width - 180, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            overall_color,
            2,
        )
        y_offset += line_height + 5

        # Statistics
        cv2.putText(
            frame,
            f"Overall Rate: {detection_rate:.1%}",
            (width - 340, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            self.colors["text"],
            1,
        )
        y_offset += line_height
        cv2.putText(
            frame,
            f"5s Rolling Rate: {rolling_rate:.1%}",
            (width - 340, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            self.colors["text"],
            1,
        )
        y_offset += line_height + 5

        # Recency weighting information
        if overall_rate is not None and recent_rate is not None:
            # Recency weighting title
            cv2.putText(
                frame,
                "Recency Weighting:",
                (width - 340, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                self.colors["text"],
                2,
            )
            y_offset += line_height

            # Overall and recent rates
            cv2.putText(
                frame,
                f"  Window: {overall_rate:.1%} Recent: {recent_rate:.1%}",
                (width - 335, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                self.colors["text"],
                1,
            )
            y_offset += line_height

            # Detection decision
            if recency_decision is not None:
                decision_text = "DETECTED" if recency_decision else "NOT DETECTED"
                decision_color = (0, 255, 0) if recency_decision else (0, 0, 255)

                cv2.putText(
                    frame,
                    f"  Decision: {decision_text}",
                    (width - 335, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    decision_color,
                    1,
                )
                y_offset += line_height

                # Decision reason
                if decision_reason:
                    cv2.putText(
                        frame,
                        f"  Reason: {decision_reason}",
                        (width - 335, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.35,
                        self.colors["text"],
                        1,
                    )
                    y_offset += line_height

        # Display detection threshold
        cv2.putText(
            frame,
            f"Threshold: {threshold:.1%}",
            (width - 340, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            self.colors["text"],
            1,
        )
        y_offset += line_height

        # Performance information
        processed_frames = results.get("_processed_frame_count", 0)
        processing_rate = (
            (processed_frames / self.frame_count) if self.frame_count > 0 else 0
        )
        cv2.putText(
            frame,
            f"Frames: {self.frame_count} ({processed_frames} processed)",
            (width - 340, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            self.colors["text"],
            1,
        )
        y_offset += line_height
        cv2.putText(
            frame,
            f"Skip: 1:{self.frame_skip} ({processing_rate:.1%} processed)",
            (width - 340, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            self.colors["text"],
            1,
        )
        y_offset += line_height
        cv2.putText(
            frame,
            f"Time: {elapsed_time:.1f}s",
            (width - 340, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            self.colors["text"],
            1,
        )

        # Detection method legend
        y_offset = height - 90
        cv2.putText(
            frame,
            "Legend:",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.colors["text"],
            2,
        )
        y_offset += 22

        legend_items = []

        # Add facial recognition to legend if enabled
        if is_facial_recognition_enabled() and self.known_encodings:
            legend_items.append(("Target Person", "facial_recognition"))
            legend_items.append(("Unknown Person", "unknown_person"))

        legend_items.extend(
            [
                ("MediaPipe Face", "mediapipe_face"),
                ("Motion", "motion"),
            ]
        )

        for method_name, method_key in legend_items:
            if method_key == "mediapipe_face" and self.face_mesh is None:
                continue
            if method_key == "facial_recognition" and not self.known_encodings:
                continue
            cv2.rectangle(
                frame,
                (10, y_offset - 12),
                (25, y_offset + 2),
                self.colors[method_key],
                -1,
            )
            cv2.putText(
                frame,
                method_name,
                (35, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                self.colors["text"],
                1,
            )
            y_offset += 18

    def get_screen_resolution(self):
        """Get screen resolution for fullscreen mode."""
        try:
            import tkinter as tk

            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            return screen_width, screen_height
        except (ImportError, Exception):
            # Fallback to common resolution if tkinter fails
            return 1920, 1080

    def run_visual_detection(self, duration=None):
        """Run visual detection with live camera feed."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return

        # ✅ PERFORMANCE FIX: Optimize camera capture
        print("⚙️ Optimizing camera for real-time performance...")

        # Set camera buffer to minimum to avoid frame accumulation
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Set optimal resolution for performance (can adjust as needed)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Set FPS (will use what camera supports)
        cap.set(cv2.CAP_PROP_FPS, 30)

        # Check actual camera properties
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        buffer_size = int(cap.get(cv2.CAP_PROP_BUFFERSIZE))

        print(
            f"📹 Camera: {actual_width}x{actual_height} @ {actual_fps:.1f}fps, buffer: {buffer_size}"
        )

        print("\n🎥 Starting optimized visual detection...")
        print("📖 Legend:")
        if self.known_encodings:
            print("   🟢 Green box = Target person recognized!")
            print("   🔴 Red box = Unknown person detected")
        print("   🟠 Orange box = MediaPipe face detected (excellent for all angles!)")
        print("   🟣 Magenta = Motion detected")
        print("\n⌨️ Controls:")
        print("   ESC or 'q' = Quit")
        print("   SPACE = Reset statistics")
        print("   'f' = Toggle fullscreen (scales camera feed)")
        print("   '+' = Reduce frame skipping (more processing, slower)")
        print("   '-' = Increase frame skipping (less processing, faster)")
        print(
            f"\n⚡ Performance: Processing every {self.frame_skip} frames for optimal speed"
        )

        start_time = time.time()
        frames_with_detection = 0
        processed_frames = 0  # ✅ Track processed frames separately
        fullscreen = False
        screen_width, screen_height = self.get_screen_resolution()

        # ✅ PERFORMANCE FIX: Frame dropping variables
        last_process_time = time.time()
        target_process_interval = (
            1.0 / 15
        )  # Process at most 15 FPS for face recognition
        frames_dropped = 0

        # Initialize variables to prevent UnboundLocalError
        detection_rate = 0.0
        elapsed_time = 0.0

        try:
            while True:
                # ✅ PERFORMANCE FIX: Read frame and check timing
                ret, frame = cap.read()
                if not ret:
                    print("❌ Can't receive frame from camera")
                    break

                self.frame_count += 1
                current_time = time.time()

                # ✅ PERFORMANCE FIX: Drop frames to maintain real-time performance
                time_since_last_process = current_time - last_process_time
                should_process_frame = (
                    time_since_last_process >= target_process_interval
                    or self.frame_count % self.frame_skip == 0
                )

                if not should_process_frame:
                    frames_dropped += 1
                    # Still show the frame but don't do heavy processing
                    display_frame = frame.copy()

                    # Add simple "dropping frames" indicator
                    cv2.putText(
                        display_frame,
                        f"Live view (dropped {frames_dropped} frames for performance)",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 0),  # Yellow
                        2,
                    )
                else:
                    # ✅ PERFORMANCE FIX: Process this frame
                    last_process_time = current_time
                    frames_dropped = 0
                    processed_frames += 1  # ✅ Count processed frames correctly

                    # Detect using all methods
                    results, annotated_frame = self.detect_all_methods(frame)
                    display_frame = annotated_frame

                    # Update statistics
                    any_detected = any(
                        v
                        for k, v in results.items()
                        if not k.startswith("_") and isinstance(v, bool)
                    )
                    if any_detected:
                        frames_with_detection += 1
                        self.detection_stats["total_detections"] += 1

                    for method, detected in results.items():
                        if (
                            not method.startswith("_")
                            and detected
                            and isinstance(detected, bool)
                        ):
                            self.detection_stats[method] += 1

                    # ✅ FIX: Calculate detection rates based on PROCESSED frames only
                    detection_rate = (
                        frames_with_detection / processed_frames
                        if processed_frames > 0
                        else 0
                    )
                    elapsed_time = time.time() - start_time

                    # Update rolling detection rate (5-second window for display)
                    self.update_rolling_detection_rate(current_time, any_detected)
                    rolling_detection_rate = self.get_rolling_detection_rate()

                    # Update frame-level detections for recency weighting
                    self.update_frame_detections(current_time, any_detected)
                    self.clear_old_frame_detections(current_time)

                    # Evaluate recency weighting for detection decision
                    overall_rate, recent_rate, recency_decision, decision_reason = (
                        self.evaluate_recency_weighting(current_time)
                    )

                    # Draw status overlay on the annotated frame before scaling
                    self.draw_status_overlay(
                        display_frame,
                        results,
                        detection_rate,
                        elapsed_time,
                        rolling_detection_rate,
                        overall_rate,
                        recent_rate,
                        recency_decision,
                        decision_reason,
                    )

                # Scale frame if in fullscreen mode
                if fullscreen:
                    # Calculate aspect ratio preserving resize
                    h, w = display_frame.shape[:2]
                    aspect_ratio = w / h

                    if screen_width / screen_height > aspect_ratio:
                        # Screen is wider, fit to height
                        new_height = screen_height
                        new_width = int(screen_height * aspect_ratio)
                    else:
                        # Screen is taller, fit to width
                        new_width = screen_width
                        new_height = int(screen_width / aspect_ratio)

                    # Resize maintaining aspect ratio
                    display_frame = cv2.resize(display_frame, (new_width, new_height))

                    # Create black background and center the frame
                    full_frame = np.zeros(
                        (screen_height, screen_width, 3), dtype=np.uint8
                    )
                    y_offset = (screen_height - new_height) // 2
                    x_offset = (screen_width - new_width) // 2
                    full_frame[
                        y_offset : y_offset + new_height,
                        x_offset : x_offset + new_width,
                    ] = display_frame
                    display_frame = full_frame

                # Store frame for motion detection (use original size)
                self.previous_frame = frame.copy()

                # Display the frame
                window_name = "Optimized Human Presence Detection - Debug View"
                cv2.imshow(window_name, display_frame)

                # ✅ PERFORMANCE FIX: Minimal wait time for responsiveness
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or key == ord("q"):  # ESC or 'q' to quit
                    break
                elif key == ord(" "):  # SPACE to reset stats
                    self.reset_statistics()
                    start_time = time.time()
                    frames_with_detection = 0
                    processed_frames = 0  # ✅ Reset local counter too
                    print("📊 Statistics reset")
                elif key == ord("f"):  # 'f' to toggle fullscreen
                    fullscreen = not fullscreen
                    if fullscreen:
                        cv2.setWindowProperty(
                            window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
                        )
                        print(
                            "🖥️ Fullscreen mode enabled - camera feed scaled to screen"
                        )
                    else:
                        cv2.setWindowProperty(
                            window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL
                        )
                        print("🪟 Windowed mode enabled - camera feed at original size")
                elif key == ord("+"):  # '+' to reduce frame skipping
                    self.frame_skip = max(1, self.frame_skip - 1)
                    print(
                        f"\n⚡ Performance: Processing every {self.frame_skip} frames "
                        f"for optimal speed"
                    )
                elif key == ord("-"):  # '-' to increase frame skipping
                    self.frame_skip += 1
                    print(
                        f"\n⚡ Performance: Processing every {self.frame_skip} frames "
                        f"for optimal speed"
                    )

                # Check duration limit
                if duration and elapsed_time >= duration:
                    print(f"\n⏱️ Duration limit reached ({duration}s)")
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()

            # Clean up MediaPipe resources
            if self.face_mesh is not None:
                try:
                    self.face_mesh.close()
                except Exception as e:
                    print(f"Warning: Error closing MediaPipe face mesh: {e}")

            # Print final statistics
            self.print_final_stats(detection_rate, elapsed_time, processed_frames)

    def reset_statistics(self):
        """Reset detection statistics."""
        self.frame_count = 0
        self.processed_frame_count = 0  # Reset this too for consistency
        self.detection_stats = {
            "facial_recognition": 0,
            "mediapipe_face": 0,
            "motion": 0,
            "total_detections": 0,
        }
        # Reset rolling window and confidence tracking
        self.detection_events = []
        self.recognition_confidences = []
        self.frame_detections = []

    def print_final_stats(self, detection_rate, elapsed_time, processed_frames=None):
        """Print final detection statistics."""
        print("\n" + "=" * 50)
        print("📊 FINAL DETECTION STATISTICS")
        print("=" * 50)
        print(f"⏱️  Total time: {elapsed_time:.1f}s")
        print(f"🎞️  Total frames: {self.frame_count}")

        # Use passed processed_frames or fall back to self.processed_frame_count
        actual_processed = (
            processed_frames
            if processed_frames is not None
            else self.processed_frame_count
        )

        processed_percent = (
            (actual_processed / self.frame_count * 100) if self.frame_count > 0 else 0
        )
        print(f"⚡ Processed frames: {actual_processed} ({processed_percent:.1f}%)")
        print(f"🔄 Frame skip ratio: 1:{self.frame_skip}")
        print(f"📈 Detection rate (processed frames): {detection_rate:.1%}")
        print(f"🎯 Detection threshold: {get_detection_param('threshold'):.1%}")
        threshold_met = detection_rate >= get_detection_param("threshold")
        status = "MET" if threshold_met else "NOT MET"
        print(f"✅ Threshold {status}")
        print()
        print("Detection method breakdown:")
        for method, count in self.detection_stats.items():
            if method == "total_detections":
                continue
            if method == "mediapipe_face" and self.face_mesh is None:
                print(f"  🔸 {method.replace('_', ' ').title()}: DISABLED")
                continue
            percentage = (count / self.frame_count * 100) if self.frame_count > 0 else 0
            processed_percentage = (
                (count / self.processed_frame_count * 100)
                if self.processed_frame_count > 0
                else 0
            )
            print(
                f"  🔸 {method.replace('_', ' ').title()}: {count} frames "
                f"({percentage:.1f}% total, {processed_percentage:.1f}% processed)"
            )

        if self.last_detection_method:
            print(f"\n🔍 Most recent detection method: {self.last_detection_method}")

        # Performance summary
        fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0
        processing_fps = (
            self.processed_frame_count / elapsed_time if elapsed_time > 0 else 0
        )
        print("\n⚡ Performance Summary:")
        print(f"   Camera FPS: {fps:.1f}")
        print(f"   Processing FPS: {processing_fps:.1f}")
        efficiency_text = (
            f"   Efficiency: {(processing_fps/fps*100):.1f}% of camera frames processed"
            if fps > 0
            else ""
        )
        if efficiency_text:
            print(efficiency_text)
        print("=" * 50)


def main():
    """Main function for visual face detection debugging."""
    parser = argparse.ArgumentParser(
        description="Visual debugging tool for optimized human presence detection."
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=None,
        help="Duration to run detection (seconds). Default: unlimited",
    )
    parser.add_argument(
        "--test-config",
        action="store_true",
        help="Test configuration and detection loading only",
    )
    args = parser.parse_args()

    print("🔍 Optimized Human Presence Detection - Visual Debug Tool")
    print("=" * 60)

    detector = VisualFaceDetector()

    # Load detection methods
    if not detector.load_detection_methods():
        print("❌ Failed to load detection methods")
        return 1

    # Print configuration info
    print("\n⚙️ Configuration:")
    print(f"   Detection threshold: {get_detection_param('threshold'):.1%}")
    print(f"   Motion min area: {get_detection_method_param('motion', 'min_area')}")
    print(f"   MediaPipe enabled: {is_detection_method_enabled('mediapipe_face')}")

    if args.test_config:
        print("\n✅ Configuration test completed successfully")
        return 0

    # Run visual detection
    try:
        detector.run_visual_detection(args.duration)
    except KeyboardInterrupt:
        print("\n\n⛔ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during detection: {e}")
        return 1

    print("\n👋 Visual detection completed")
    return 0


if __name__ == "__main__":
    exit(main())
