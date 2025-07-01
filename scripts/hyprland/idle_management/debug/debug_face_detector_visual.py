#!/usr/bin/env python3

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import centralized configuration
from config import get_cascade_file, get_detection_param  # noqa: E402


class VisualFaceDetector:
    """Visual debugging tool for face detection system."""

    def __init__(self):
        self.face_cascade = None
        self.profile_cascade = None
        self.upperbody_cascade = None
        self.previous_frame = None

        # Detection statistics
        self.frame_count = 0
        self.detection_stats = {
            "frontal_face": 0,
            "profile_face": 0,
            "upper_body": 0,
            "motion": 0,
            "total_detections": 0,
        }

        # Colors for different detection types
        self.colors = {
            "frontal_face": (0, 255, 0),  # Green
            "profile_face": (255, 0, 0),  # Blue
            "upper_body": (0, 165, 255),  # Orange
            "motion": (255, 0, 255),  # Magenta
            "text": (255, 255, 255),  # White
            "background": (0, 0, 0),  # Black
        }

    def load_cascades(self):
        """Load all cascade classifiers."""
        print("Loading cascade classifiers...")

        # Load required cascades
        face_cascade_path = get_cascade_file("frontal_face")
        profile_cascade_path = get_cascade_file("profile_face")
        upperbody_cascade_path = get_cascade_file("upper_body")

        if not face_cascade_path.exists() or not profile_cascade_path.exists():
            print("❌ Required cascade files not found!")
            print(f"   Frontal face: {face_cascade_path}")
            print(f"   Profile face: {profile_cascade_path}")
            return False

        self.face_cascade = cv2.CascadeClassifier(str(face_cascade_path))
        self.profile_cascade = cv2.CascadeClassifier(str(profile_cascade_path))

        # Load optional upper body cascade
        if upperbody_cascade_path.exists():
            self.upperbody_cascade = cv2.CascadeClassifier(str(upperbody_cascade_path))
            print(f"✓ Upper body cascade loaded from {upperbody_cascade_path}")
        else:
            print(f"⚠ Upper body cascade not found at {upperbody_cascade_path}")
            print("  Upper body detection will be disabled")

        # Verify cascades loaded correctly
        if self.face_cascade.empty() or self.profile_cascade.empty():
            print("❌ Failed to load required face detection cascades")
            return False

        if self.upperbody_cascade is not None and self.upperbody_cascade.empty():
            print("⚠ Failed to load upper body cascade, disabling upper body detection")
            self.upperbody_cascade = None

        print("✓ Cascade classifiers loaded successfully")
        print("✓ Frontal face detection: enabled")
        print("✓ Profile face detection: enabled")
        print(
            f"✓ Upper body detection: {'enabled' if self.upperbody_cascade else 'disabled'}"
        )
        print("✓ Motion detection: enabled")

        return True

    def detect_motion(self, frame1, frame2, debug_display=None):
        """Detect motion between two frames with optional debug display."""
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

    def detect_all_methods(self, frame):
        """Detect using all available methods and return results with visual annotations."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        results = {}
        annotated_frame = frame.copy()

        # Get detection parameters from config
        scale_factor = get_detection_param("cascade_scale_factor")
        min_neighbors_face = get_detection_param("cascade_min_neighbors_face")
        min_neighbors_upperbody = get_detection_param("cascade_min_neighbors_upperbody")

        # Frontal face detection
        faces = self.face_cascade.detectMultiScale(
            gray, scale_factor, min_neighbors_face
        )
        results["frontal_face"] = len(faces) > 0
        for x, y, w, h in faces:
            cv2.rectangle(
                annotated_frame, (x, y), (x + w, y + h), self.colors["frontal_face"], 3
            )
            cv2.putText(
                annotated_frame,
                "Frontal Face",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                self.colors["frontal_face"],
                2,
            )

        # Profile face detection
        profiles = self.profile_cascade.detectMultiScale(
            gray, scale_factor, min_neighbors_face
        )
        results["profile_face"] = len(profiles) > 0
        for x, y, w, h in profiles:
            cv2.rectangle(
                annotated_frame, (x, y), (x + w, y + h), self.colors["profile_face"], 3
            )
            cv2.putText(
                annotated_frame,
                "Profile Face",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                self.colors["profile_face"],
                2,
            )

        # Upper body detection
        results["upper_body"] = False
        if self.upperbody_cascade is not None:
            upperbodies = self.upperbody_cascade.detectMultiScale(
                gray, scale_factor, min_neighbors_upperbody
            )
            results["upper_body"] = len(upperbodies) > 0
            for x, y, w, h in upperbodies:
                cv2.rectangle(
                    annotated_frame,
                    (x, y),
                    (x + w, y + h),
                    self.colors["upper_body"],
                    3,
                )
                cv2.putText(
                    annotated_frame,
                    "Upper Body",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    self.colors["upper_body"],
                    2,
                )

        # Motion detection
        results["motion"] = False
        if self.previous_frame is not None:
            results["motion"] = self.detect_motion(
                self.previous_frame, frame, annotated_frame
            )

        return results, annotated_frame

    def draw_status_overlay(self, frame, results, detection_rate, elapsed_time):
        """Draw status information overlay on the frame."""
        height, width = frame.shape[:2]

        # Semi-transparent overlay for status
        overlay = frame.copy()
        cv2.rectangle(
            overlay, (width - 320, 0), (width, 280), self.colors["background"], -1
        )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        y_offset = 30
        line_height = 25

        # Title
        cv2.putText(
            frame,
            "Human Presence Detection",
            (width - 315, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.colors["text"],
            2,
        )
        y_offset += line_height + 10

        # Detection status for each method
        methods = [
            ("Frontal Face", "frontal_face"),
            ("Profile Face", "profile_face"),
            ("Upper Body", "upper_body"),
            ("Motion", "motion"),
        ]

        for method_name, method_key in methods:
            if method_key == "upper_body" and self.upperbody_cascade is None:
                status = "DISABLED"
                color = (128, 128, 128)  # Gray
            else:
                status = (
                    "DETECTED" if results.get(method_key, False) else "NOT DETECTED"
                )
                color = (
                    self.colors[method_key]
                    if results.get(method_key, False)
                    else (128, 128, 128)
                )

            cv2.putText(
                frame,
                f"{method_name}:",
                (width - 310, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                self.colors["text"],
                1,
            )
            cv2.putText(
                frame,
                status,
                (width - 180, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )
            y_offset += line_height

        y_offset += 10

        # Overall detection status
        threshold = get_detection_param("threshold")
        any_detected = any(results.values())
        overall_status = "PRESENT" if any_detected else "NOT PRESENT"
        overall_color = (0, 255, 0) if any_detected else (0, 0, 255)

        cv2.putText(
            frame,
            "Overall Status:",
            (width - 310, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.colors["text"],
            2,
        )
        cv2.putText(
            frame,
            overall_status,
            (width - 150, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            overall_color,
            2,
        )
        y_offset += line_height + 5

        # Statistics
        cv2.putText(
            frame,
            f"Detection Rate: {detection_rate:.1%}",
            (width - 310, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.colors["text"],
            1,
        )
        y_offset += line_height
        cv2.putText(
            frame,
            f"Threshold: {threshold:.1%}",
            (width - 310, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.colors["text"],
            1,
        )
        y_offset += line_height
        cv2.putText(
            frame,
            f"Frame: {self.frame_count}",
            (width - 310, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.colors["text"],
            1,
        )
        y_offset += line_height
        cv2.putText(
            frame,
            f"Time: {elapsed_time:.1f}s",
            (width - 310, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            self.colors["text"],
            1,
        )

        # Detection method legend
        y_offset = height - 120
        cv2.putText(
            frame,
            "Legend:",
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            self.colors["text"],
            2,
        )
        y_offset += 25

        legend_items = [
            ("Frontal Face", "frontal_face"),
            ("Profile Face", "profile_face"),
            ("Upper Body", "upper_body"),
            ("Motion", "motion"),
        ]

        for method_name, method_key in legend_items:
            if method_key == "upper_body" and self.upperbody_cascade is None:
                continue
            cv2.rectangle(
                frame, (10, y_offset - 15), (25, y_offset), self.colors[method_key], -1
            )
            cv2.putText(
                frame,
                method_name,
                (35, y_offset - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                self.colors["text"],
                1,
            )
            y_offset += 20

    def run_visual_detection(self, duration=None):
        """Run visual detection with live camera feed."""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return

        print("\n🎥 Starting visual detection...")
        print("📖 Legend:")
        print("   🟢 Green box = Frontal face detected")
        print("   🔵 Blue box = Profile face detected")
        print("   🟠 Orange box = Upper body detected")
        print("   🟣 Magenta = Motion detected")
        print("\n⌨️ Controls:")
        print("   ESC or 'q' = Quit")
        print("   SPACE = Reset statistics")
        print("   'f' = Toggle fullscreen")

        start_time = time.time()
        frames_with_detection = 0
        fullscreen = False

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Can't receive frame from camera")
                    break

                self.frame_count += 1

                # Detect using all methods
                results, annotated_frame = self.detect_all_methods(frame)

                # Update statistics
                if any(results.values()):
                    frames_with_detection += 1
                    self.detection_stats["total_detections"] += 1

                for method, detected in results.items():
                    if detected:
                        self.detection_stats[method] += 1

                # Calculate detection rate
                detection_rate = (
                    frames_with_detection / self.frame_count
                    if self.frame_count > 0
                    else 0
                )
                elapsed_time = time.time() - start_time

                # Draw status overlay
                self.draw_status_overlay(
                    annotated_frame, results, detection_rate, elapsed_time
                )

                # Store frame for motion detection
                self.previous_frame = frame.copy()

                # Display the frame
                window_name = "Enhanced Human Presence Detection - Debug View"
                cv2.imshow(window_name, annotated_frame)

                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or key == ord("q"):  # ESC or 'q' to quit
                    break
                elif key == ord(" "):  # SPACE to reset stats
                    self.reset_statistics()
                    start_time = time.time()
                    frames_with_detection = 0
                    print("📊 Statistics reset")
                elif key == ord("f"):  # 'f' to toggle fullscreen
                    fullscreen = not fullscreen
                    if fullscreen:
                        cv2.setWindowProperty(
                            window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
                        )
                    else:
                        cv2.setWindowProperty(
                            window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL
                        )

                # Check duration limit
                if duration and elapsed_time >= duration:
                    print(f"\n⏱️ Duration limit reached ({duration}s)")
                    break

        finally:
            cap.release()
            cv2.destroyAllWindows()

            # Print final statistics
            self.print_final_stats(detection_rate, elapsed_time)

    def reset_statistics(self):
        """Reset detection statistics."""
        self.frame_count = 0
        self.detection_stats = {
            "frontal_face": 0,
            "profile_face": 0,
            "upper_body": 0,
            "motion": 0,
            "total_detections": 0,
        }

    def print_final_stats(self, detection_rate, elapsed_time):
        """Print final detection statistics."""
        print("\n" + "=" * 50)
        print("📊 FINAL DETECTION STATISTICS")
        print("=" * 50)
        print(f"⏱️  Total time: {elapsed_time:.1f}s")
        print(f"🎞️  Total frames: {self.frame_count}")
        print(f"📈 Overall detection rate: {detection_rate:.1%}")
        print(f"🎯 Detection threshold: {get_detection_param('threshold'):.1%}")
        threshold_met = detection_rate >= get_detection_param("threshold")
        status = "MET" if threshold_met else "NOT MET"
        print(f"✅ Threshold {status}")
        print()
        print("Detection method breakdown:")
        for method, count in self.detection_stats.items():
            if method == "total_detections":
                continue
            if method == "upper_body" and self.upperbody_cascade is None:
                print(f"  🔸 {method.replace('_', ' ').title()}: DISABLED")
                continue
            percentage = (count / self.frame_count * 100) if self.frame_count > 0 else 0
            print(
                f"  🔸 {method.replace('_', ' ').title()}: {count} frames ({percentage:.1f}%)"
            )
        print("=" * 50)


def main():
    """Main function for visual face detection debugging."""
    parser = argparse.ArgumentParser(
        description="Visual debugging tool for enhanced human presence detection."
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
        help="Test configuration and cascade loading only",
    )
    args = parser.parse_args()

    print("🔍 Enhanced Human Presence Detection - Visual Debug Tool")
    print("=" * 60)

    detector = VisualFaceDetector()

    # Load cascades
    if not detector.load_cascades():
        print("❌ Failed to load cascade classifiers")
        return 1

    # Print configuration info
    print("\n⚙️ Configuration:")
    print(f"   Detection threshold: {get_detection_param('threshold'):.1%}")
    print(f"   Scale factor: {get_detection_param('cascade_scale_factor')}")
    print(
        f"   Min neighbors (face): {get_detection_param('cascade_min_neighbors_face')}"
    )
    print(
        f"   Min neighbors (body): {get_detection_param('cascade_min_neighbors_upperbody')}"
    )
    print(f"   Motion min area: {get_detection_param('motion_min_area')}")

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
