#!/usr/bin/env python3

"""
Facial Recognition Setup and Calibration Tool

This script helps users set up and calibrate facial recognition for the idle management system.
It guides through dependency installation, reference image collection, and system testing.
"""

import argparse
import logging
import pickle
import sys
import time

import cv2
import numpy as np
from colorama import Fore, Style

# Import centralized configuration
from config import (
    ensure_directories,
    get_facial_recognition_param,
    is_facial_recognition_enabled,
    validate_config,
)

# Try to import face_recognition
try:
    import face_recognition

    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False


def setup_logging():
    """Set up logging for the setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def check_dependencies():
    """Check if all required dependencies are installed."""
    logging.info("🔍 Checking dependencies...")

    missing = []

    # Check OpenCV
    try:
        import cv2 as _cv2  # noqa: F401

        logging.info("✓ OpenCV installed")
    except ImportError:
        missing.append("opencv-python")

    # Check face_recognition
    if not FACE_RECOGNITION_AVAILABLE:
        missing.append("face_recognition")
        missing.append("dlib")
    else:
        logging.info("✓ face_recognition library installed")

    if missing:
        logging.error("❌ Missing dependencies:")
        for dep in missing:
            logging.error(f"   - {dep}")
        logging.error("\nInstall with:")
        logging.error("   pip install " + " ".join(missing))
        logging.error("\nFor dlib compilation issues, try:")
        logging.error("   conda install -c conda-forge dlib")
        logging.error("   pip install face_recognition")
        return False

    logging.info("✅ All dependencies installed")
    return True


def check_camera():
    """Check if camera is accessible."""
    import cv2

    logging.info("📷 Checking camera access...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("❌ Cannot access camera at /dev/video0")
        logging.error("Check camera permissions and availability")
        return False

    # Try to read a frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        logging.error("❌ Cannot read from camera")
        return False

    logging.info("✅ Camera accessible")
    return True


def enable_facial_recognition():
    """Guide user through enabling facial recognition in config."""
    if is_facial_recognition_enabled():
        logging.info("✅ Facial recognition already enabled in config")
        return True

    logging.warning("⚠️  Facial recognition is disabled in config.py")
    response = input("Enable facial recognition? (y/N): ").strip().lower()

    if response == "y":
        logging.info("📝 To enable facial recognition:")
        logging.info("1. Edit ~/.config/scripts/hyprland/idle_management/config.py")
        logging.info('2. Set DETECTION_PARAMS["facial_recognition"]["enabled"] = True')
        logging.info("3. Run this script again")
        return False
    else:
        logging.info("Facial recognition setup cancelled")
        return False


def setup_reference_directory():
    """Create and set up the reference images directory."""
    logging.info("📁 Setting up reference images directory...")

    ref_dir = get_facial_recognition_param("reference_images_dir")

    try:
        ensure_directories()
        logging.info(f"✅ Reference directory ready: {ref_dir}")
        return ref_dir
    except Exception as e:
        logging.error(f"❌ Failed to create directory: {e}")
        return None


def capture_reference_images(ref_dir, num_images=10):
    """Guide user through capturing reference images with face detection feedback."""
    import cv2

    # Find existing reference images to continue numbering
    existing_images = sorted([f for f in ref_dir.glob("reference_*.jpg")])
    start_number = len(existing_images)

    if existing_images:
        logging.info(f"📁 Found {len(existing_images)} existing reference images")
        logging.info(
            f"📸 Will add {num_images} new images starting from "
            f"reference_{start_number:02d}.jpg"
        )
    else:
        logging.info(f"📸 Capturing {num_images} reference images...")

    logging.info("\nInstructions:")
    logging.info("- Look directly at the camera")
    logging.info("- GREEN BOX = Face detected, ready to capture!")
    logging.info("- RED BOX = Face detected but poor quality")
    logging.info("- Press SPACE to capture when GREEN BOX is shown")
    logging.info("- Press ESC to finish early")
    logging.info("- Try different:")
    logging.info("  * Lighting conditions (bright, dim)")
    logging.info("  * Slight head angles (left, right, up, down)")
    logging.info("  * Expressions (neutral, slight smile)")
    logging.info("  * With/without glasses if applicable")

    input("\nPress ENTER when ready to start...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("❌ Cannot open camera")
        return 0

    captured = 0

    try:
        while captured < num_images:
            ret, frame = cap.read()
            if not ret:
                logging.error("Failed to read frame")
                break

            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)

            # Create a copy for display (with overlays) and keep original clean for saving
            display_frame = frame.copy()

            # Detect faces in current frame for visual feedback
            face_detected = False
            face_quality = "none"
            best_face_location = None

            if FACE_RECOGNITION_AVAILABLE:
                try:
                    face_locations = face_recognition.face_locations(frame, model="hog")
                    if face_locations:
                        face_detected = True

                        # Check if we can get a good encoding (quality check)
                        face_encodings = face_recognition.face_encodings(
                            frame, face_locations
                        )
                        if face_encodings and len(face_encodings) > 0:
                            # Calculate quality for each face and find the best one
                            best_quality = 0.0
                            face_qualities = []

                            for (top, right, bottom, left), encoding in zip(
                                face_locations, face_encodings
                            ):
                                # Face size factor (larger faces = better quality)
                                face_area = (right - left) * (bottom - top)
                                size_factor = min(
                                    face_area / (frame.shape[0] * frame.shape[1] * 0.1),
                                    1.0,
                                )

                                # Encoding quality (check if encoding is strong)
                                encoding_strength = np.linalg.norm(encoding)
                                strength_factor = min(encoding_strength / 1.0, 1.0)

                                # Combined quality score for this face
                                current_quality = (
                                    size_factor * 0.7 + strength_factor * 0.3
                                )

                                face_qualities.append(current_quality)

                                # Track the best face
                                if current_quality > best_quality:
                                    best_quality = current_quality
                                    best_face_location = (top, right, bottom, left)

                            # Use best face quality for capture decision
                            face_quality = "good" if best_quality > 0.6 else "poor"
                        else:
                            face_quality = "poor"

                        # Draw bounding boxes around detected faces on DISPLAY frame only
                        for i, (top, right, bottom, left) in enumerate(face_locations):
                            is_best_face = (
                                top,
                                right,
                                bottom,
                                left,
                            ) == best_face_location

                            if is_best_face:
                                # Best face: green if good quality, red if poor
                                color = (
                                    (0, 255, 0)
                                    if face_quality == "good"
                                    else (0, 0, 255)
                                )
                                thickness = 4  # Thicker border for best face
                                label_prefix = "BEST: "
                            else:
                                # Other faces: orange (not used for capture decision)
                                color = (0, 165, 255)  # Orange
                                thickness = 2
                                label_prefix = "OTHER: "

                            cv2.rectangle(
                                display_frame,
                                (left, top),
                                (right, bottom),
                                color,
                                thickness,
                            )

                            # Add quality label on DISPLAY frame only
                            if is_best_face:
                                label = (
                                    f"{label_prefix}READY TO CAPTURE"
                                    if face_quality == "good"
                                    else f"{label_prefix}POOR QUALITY"
                                )
                            else:
                                if i < len(face_qualities):
                                    current_face_quality = face_qualities[i]
                                    label = (
                                        f"{label_prefix}Q: {current_face_quality:.2f}"
                                    )
                                else:
                                    label = f"{label_prefix}No encoding"

                            cv2.putText(
                                display_frame,
                                label,
                                (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                color,
                                2,
                            )

                except Exception as e:
                    logging.debug(f"Face detection error: {e}")

            # Add instructions overlay on DISPLAY frame only
            status_color = (
                (0, 255, 0)
                if face_quality == "good"
                else (0, 0, 255) if face_detected else (255, 255, 255)
            )
            status_text = (
                f"Captured: {captured}/{num_images} (#{start_number + captured})"
            )

            cv2.putText(
                display_frame,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                status_color,
                2,
            )

            # Show face detection status on DISPLAY frame only
            if face_detected:
                if face_quality == "good":
                    instruction = "FACE DETECTED - SPACE: Capture!"
                    instruction_color = (0, 255, 0)
                else:
                    instruction = "FACE DETECTED - Improve position/lighting"
                    instruction_color = (0, 0, 255)
            else:
                instruction = "Looking for face..."
                instruction_color = (255, 255, 255)

            cv2.putText(
                display_frame,
                instruction,
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                instruction_color,
                2,
            )

            cv2.putText(
                display_frame,
                "ESC: Finish",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Reference Image Capture", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord(" "):  # Space to capture
                if face_quality == "good":
                    filename = ref_dir / f"reference_{start_number + captured:02d}.jpg"
                    # Save the CLEAN frame without any overlays
                    cv2.imwrite(str(filename), frame)
                    logging.info(
                        f"📸 Captured clean image {captured + 1}: {filename.name}"
                    )
                    if len(face_locations) > 1:
                        logging.info(
                            f"   📊 Multiple faces detected: "
                            f"selected best of {len(face_locations)} faces"
                        )
                    captured += 1
                    time.sleep(0.5)  # Prevent accidental double capture
                elif face_detected:
                    logging.warning(
                        "⚠️ Face detected but quality too poor. "
                        "Adjust position/lighting and try again."
                    )
                else:
                    logging.warning(
                        "⚠️ No face detected. Position yourself in front of camera and try again."
                    )

            elif key == 27:  # ESC to exit
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    total_images = start_number + captured
    logging.info(f"✅ Captured {captured} new clean reference images")
    logging.info(f"📁 Total reference images: {total_images}")

    # Clear cached encodings so they get regenerated with new images
    encodings_file = ref_dir / "encodings.pkl"
    if encodings_file.exists():
        encodings_file.unlink()
        logging.info("🔄 Cleared cached encodings - will regenerate with new images")

    return captured


def auto_capture_reference_images(ref_dir, num_images=None, quality_threshold=0.8):
    """Automatically capture reference images when good quality faces are detected."""
    import cv2

    # Find existing reference images to continue numbering
    existing_images = sorted([f for f in ref_dir.glob("reference_*.jpg")])
    start_number = len(existing_images)

    if existing_images:
        logging.info(f"📁 Found {len(existing_images)} existing reference images")
        if num_images:
            logging.info(
                f"🤖 Will automatically capture {num_images} new images starting from "
                f"reference_{start_number:02d}.jpg"
            )
        else:
            logging.info(
                f"🤖 Will automatically capture images starting from "
                f"reference_{start_number:02d}.jpg (until ESC)"
            )
    else:
        if num_images:
            logging.info(f"🤖 Automatically capturing {num_images} reference images...")
        else:
            logging.info("🤖 Automatically capturing reference images (until ESC)...")

    if not FACE_RECOGNITION_AVAILABLE:
        logging.error("❌ face_recognition library not available")
        return 0

    logging.info("\nAutomatic capture mode:")
    logging.info("- Position yourself in front of the camera")
    logging.info("- Move your head naturally for variety")
    logging.info("- Try different lighting and expressions")
    logging.info("- Images will be captured automatically when quality is good")
    logging.info("- Press ESC to stop")

    input("\nPress ENTER when ready to start automatic capture...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("❌ Cannot open camera")
        return 0

    captured = 0
    last_capture_time = 0
    min_capture_interval = 2.0  # Minimum seconds between captures
    consecutive_good_frames = 0
    frames_needed = 3  # Need N consecutive good frames before capturing

    try:
        while num_images is None or captured < num_images:
            ret, frame = cap.read()
            if not ret:
                logging.error("Failed to read frame")
                break

            # Flip frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)

            # Create a copy for display
            display_frame = frame.copy()

            # Detect faces and check quality
            face_detected = False
            face_quality_score = 0.0
            best_face_location = None
            current_time = time.time()

            try:
                face_locations = face_recognition.face_locations(frame, model="hog")
                if face_locations:
                    face_detected = True

                    # Check face quality
                    face_encodings = face_recognition.face_encodings(
                        frame, face_locations
                    )

                    if face_encodings and len(face_encodings) > 0:
                        # Calculate quality score for each face and find the best one
                        best_quality = 0.0
                        face_qualities = []

                        for (top, right, bottom, left), encoding in zip(
                            face_locations, face_encodings
                        ):
                            # Face size factor (larger faces = better quality)
                            face_area = (right - left) * (bottom - top)
                            size_factor = min(
                                face_area / (frame.shape[0] * frame.shape[1] * 0.1), 1.0
                            )

                            # Encoding quality (check if encoding is strong)
                            encoding_strength = np.linalg.norm(encoding)
                            strength_factor = min(encoding_strength / 1.0, 1.0)

                            # Combined quality score for this face
                            current_quality = size_factor * 0.7 + strength_factor * 0.3

                            face_qualities.append(current_quality)

                            # Track the best face
                            if current_quality > best_quality:
                                best_quality = current_quality
                                best_face_location = (top, right, bottom, left)

                        # Use the best face's quality score
                        face_quality_score = best_quality

                    # Draw bounding boxes for all faces, highlight the best one
                    for i, (top, right, bottom, left) in enumerate(face_locations):
                        is_best_face = (top, right, bottom, left) == best_face_location

                        if is_best_face:
                            # Best face: green if good quality, yellow if poor
                            is_good_quality = face_quality_score >= quality_threshold
                            color = (0, 255, 0) if is_good_quality else (0, 255, 255)
                            thickness = 4  # Thicker border for best face
                            label_prefix = "BEST: "
                        else:
                            # Other faces: orange (not used for capture decision)
                            color = (0, 165, 255)  # Orange
                            thickness = 2
                            label_prefix = "OTHER: "

                        cv2.rectangle(
                            display_frame,
                            (left, top),
                            (right, bottom),
                            color,
                            thickness,
                        )

                        # Add quality score label
                        if i < len(face_qualities):
                            current_face_quality = face_qualities[i]
                            label = f"{label_prefix}Q: {current_face_quality:.2f}"
                        else:
                            label = f"{label_prefix}No encoding"

                        cv2.putText(
                            display_frame,
                            label,
                            (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            color,
                            2,
                        )

                    # Check if we should capture (based on BEST face quality)
                    if (
                        face_quality_score >= quality_threshold
                        and current_time - last_capture_time >= min_capture_interval
                    ):
                        consecutive_good_frames += 1

                        if consecutive_good_frames >= frames_needed:
                            filename = (
                                ref_dir / f"reference_{start_number + captured:02d}.jpg"
                            )
                            # Save the CLEAN frame without any overlays
                            cv2.imwrite(str(filename), frame)
                            logging.info(
                                f"🤖 Auto-captured image {captured + 1}: {filename.name} "
                                f"(best face quality: {face_quality_score:.2f})"
                            )
                            if len(face_locations) > 1:
                                logging.info(
                                    f"   📊 Multiple faces detected: "
                                    f"selected best of {len(face_locations)} faces"
                                )
                            captured += 1
                            last_capture_time = current_time
                            consecutive_good_frames = 0
                    else:
                        if face_quality_score < quality_threshold:
                            consecutive_good_frames = 0

            except Exception as e:
                logging.debug(f"Face detection error: {e}")
                consecutive_good_frames = 0

            # Add status overlay on display frame
            progress_color = (0, 255, 0) if face_detected else (255, 255, 255)
            if num_images:
                status_text = f"Auto-captured: {captured}/{num_images}"
            else:
                status_text = f"Auto-captured: {captured} (ESC to stop)"
            cv2.putText(
                display_frame,
                status_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                progress_color,
                2,
            )

            # Show capture status
            if face_detected:
                if face_quality_score >= quality_threshold:
                    if consecutive_good_frames < frames_needed:
                        status = (
                            f"GOOD QUALITY - Stabilizing "
                            f"{consecutive_good_frames}/{frames_needed}"
                        )
                        status_color = (0, 255, 255)
                    else:
                        status = "CAPTURING..."
                        status_color = (0, 255, 0)
                else:
                    status = f"Low quality ({face_quality_score:.2f}) - Keep moving naturally"
                    status_color = (255, 165, 0)
            else:
                status = "Looking for face..."
                status_color = (255, 255, 255)

            cv2.putText(
                display_frame,
                status,
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                status_color,
                2,
            )

            cv2.putText(
                display_frame,
                f"Quality threshold: {quality_threshold:.2f}",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                display_frame,
                "ESC: Stop capture",
                (10, display_frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

            cv2.imshow("Automatic Reference Capture", display_frame)

            if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    total_images = start_number + captured
    logging.info(f"✅ Auto-captured {captured} new clean reference images")
    logging.info(f"📁 Total reference images: {total_images}")

    # Clear cached encodings so they get regenerated with new images
    encodings_file = ref_dir / "encodings.pkl"
    if encodings_file.exists():
        encodings_file.unlink()
        logging.info("🔄 Cleared cached encodings - will regenerate with new images")

    return captured


def test_live_recognition():
    """Test live facial recognition with the camera."""
    import cv2

    logging.info("🎥 Testing live facial recognition...")
    logging.info("Instructions:")
    logging.info("- Look at the camera")
    logging.info("- Recognition results will be shown")
    logging.info("- Press ESC to exit")

    if not FACE_RECOGNITION_AVAILABLE:
        logging.error("❌ face_recognition library not available")
        return

    # Load reference encodings
    from face_detector import load_reference_encodings

    try:
        known_encodings = load_reference_encodings()
        if not known_encodings:
            logging.error("❌ No reference encodings available")
            return

        logging.info(f"✅ Loaded {len(known_encodings)} reference encodings")

    except Exception as e:
        logging.error(f"❌ Failed to load encodings: {e}")
        return

    input("Press ENTER to start live test...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        logging.error("❌ Cannot open camera")
        return

    tolerance = get_facial_recognition_param("tolerance")
    min_confidence = get_facial_recognition_param("min_recognition_confidence")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Flip for mirror effect
            frame = cv2.flip(frame, 1)

            try:
                # Find faces
                face_locations = face_recognition.face_locations(frame)

                if face_locations:
                    # Get encodings
                    face_encodings = face_recognition.face_encodings(
                        frame, face_locations
                    )

                    for (top, right, bottom, left), face_encoding in zip(
                        face_locations, face_encodings
                    ):
                        # Compare with known faces
                        face_distances = face_recognition.face_distance(
                            known_encodings, face_encoding
                        )

                        if len(face_distances) > 0:
                            best_distance = np.min(face_distances)
                            confidence = 1.0 - best_distance

                            # Check if recognized
                            matches = face_recognition.compare_faces(
                                known_encodings, face_encoding, tolerance=tolerance
                            )
                            recognized = any(matches) and confidence >= min_confidence

                            # Draw rectangle around face
                            color = (0, 255, 0) if recognized else (0, 0, 255)
                            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                            # Add label
                            label = (
                                f"RECOGNIZED ({confidence:.2f})"
                                if recognized
                                else f"UNKNOWN ({confidence:.2f})"
                            )
                            cv2.putText(
                                frame,
                                label,
                                (left, top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                color,
                                2,
                            )

                # Add status text
                cv2.putText(
                    frame,
                    f"Tolerance: {tolerance:.2f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Min Confidence: {min_confidence:.2f}",
                    (10, 55),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    "ESC: Exit",
                    (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

            except Exception as e:
                cv2.putText(
                    frame,
                    f"Error: {str(e)[:50]}",
                    (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 255),
                    1,
                )

            cv2.imshow("Live Facial Recognition Test", frame)

            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()

    logging.info("✅ Live recognition test completed")


def validate_and_generate_encodings():
    """Validate reference images and generate encodings in a single efficient pass."""
    print(
        f"\n{Fore.CYAN}🔄 Validating images and generating encodings...{Style.RESET_ALL}"
    )

    if not FACE_RECOGNITION_AVAILABLE:
        print(f"{Fore.RED}❌ face_recognition not available{Style.RESET_ALL}")
        return False

    reference_dir = get_facial_recognition_param("reference_images_dir")
    supported_formats = get_facial_recognition_param("supported_image_formats")
    encodings_file = reference_dir / "encodings.pkl"

    # Remove old cache
    if encodings_file.exists():
        encodings_file.unlink()
        print("🗑️ Removed old encodings cache")

    # Collect all reference images
    reference_images = []
    for fmt in supported_formats:
        reference_images.extend(reference_dir.glob(f"*{fmt}"))

    if not reference_images:
        print(f"{Fore.RED}❌ No reference images found{Style.RESET_ALL}")
        return False

    print(f"⚙️ Processing {len(reference_images)} images (validate + encode)...")

    good_encodings = []
    good_images = []
    deleted_count = 0

    for image_path in reference_images:
        try:
            print(f"   🔍 Processing {image_path.name}...", end=" ")

            # Load image
            image = face_recognition.load_image_file(str(image_path))

            # Try to generate encodings directly (this validates the image)
            face_encodings = face_recognition.face_encodings(
                image,
                model=get_facial_recognition_param("face_detection_model"),
                num_jitters=get_facial_recognition_param("num_jitters"),
            )

            if face_encodings:
                # Image is good - add encodings and keep track
                good_encodings.extend(face_encodings)
                good_images.append(image_path)
                print(f"✅ Generated {len(face_encodings)} encoding(s)")
            else:
                # Image is bad - delete it
                image_path.unlink()
                deleted_count += 1
                print("❌ No faces/encodings - deleted")

        except Exception as e:
            # Image is bad - delete it
            try:
                image_path.unlink()
                deleted_count += 1
                print(f"❌ Error: {str(e)[:30]}... - deleted")
            except Exception:
                print(
                    f"❌ Error: {str(e)[:20]}... - {Fore.RED}failed to delete{Style.RESET_ALL}"
                )

    # Report results
    print("\n📊 Processing complete:")
    print(
        f"   ✅ Good images: {len(good_images)} → Generated {len(good_encodings)} encodings"
    )
    print(f"   🗑️ Bad images deleted: {deleted_count}")

    # Rename good images sequentially to remove gaps
    if good_images and deleted_count > 0:
        print("\n🔄 Renaming remaining images sequentially...")

        # Sort good images by current number to maintain order
        good_images.sort(key=lambda p: p.name)

        renamed_count = 0
        for new_index, image_path in enumerate(good_images):
            expected_name = f"reference_{new_index:02d}.jpg"

            if image_path.name != expected_name:
                old_name = image_path.name
                new_path = image_path.parent / expected_name

                # Avoid conflicts by using temporary names if needed
                if new_path.exists():
                    temp_path = image_path.parent / f"temp_{new_index:02d}.jpg"
                    image_path.rename(temp_path)
                    image_path = temp_path

                image_path.rename(new_path)
                renamed_count += 1
                print(f"   📝 {old_name} → {expected_name}")

        if renamed_count > 0:
            print(f"✅ Renumbered {renamed_count} images sequentially")
        else:
            print("✅ Images already sequentially numbered")

    if not good_encodings:
        print(f"{Fore.RED}❌ No valid encodings generated!{Style.RESET_ALL}")
        return False

    # Cache the encodings
    try:
        with open(encodings_file, "wb") as f:
            pickle.dump({"encodings": good_encodings, "version": "1.0"}, f)
        print(f"✅ Cached {len(good_encodings)} face encodings to {encodings_file}")
        return True
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to cache encodings: {e}{Style.RESET_ALL}")
        return False


def smart_select_reference_images(target_count=10):
    """Intelligently select the best reference images based on quality and diversity."""
    print(
        f"\n{Fore.CYAN}🎯 Smart selection: Finding best {target_count} "
        f"reference images...{Style.RESET_ALL}"
    )

    if not FACE_RECOGNITION_AVAILABLE:
        print(f"{Fore.RED}❌ face_recognition not available{Style.RESET_ALL}")
        return False

    reference_dir = get_facial_recognition_param("reference_images_dir")
    supported_formats = get_facial_recognition_param("supported_image_formats")

    # Collect all reference images
    reference_images = []
    for fmt in supported_formats:
        reference_images.extend(reference_dir.glob(f"*{fmt}"))

    if len(reference_images) <= target_count:
        print(
            f"✅ Already have {len(reference_images)} images (≤ {target_count}), no selection needed"
        )
        return True

    print(f"📊 Analyzing {len(reference_images)} images for quality and diversity...")

    image_metrics = []

    for image_path in reference_images:
        try:
            print(f"   🔍 Analyzing {image_path.name}...", end=" ")

            # Load image
            image = face_recognition.load_image_file(str(image_path))
            h, w = image.shape[:2]

            # Get face encoding and location
            face_locations = face_recognition.face_locations(image, model="hog")
            face_encodings = face_recognition.face_encodings(image, face_locations)

            if not face_encodings or not face_locations:
                print("❌ No face detected")
                continue

            encoding = face_encodings[0]
            top, right, bottom, left = face_locations[0]

            # Calculate quality metrics
            face_area = (right - left) * (bottom - top)
            face_area_ratio = face_area / (w * h)  # Face size relative to image
            encoding_strength = np.linalg.norm(encoding)

            # Face position metrics (centered faces often better quality)
            face_center_x = (left + right) / 2 / w
            face_center_y = (top + bottom) / 2 / h
            center_distance = (
                (face_center_x - 0.5) ** 2 + (face_center_y - 0.5) ** 2
            ) ** 0.5

            # Image brightness (variety in lighting conditions)
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            brightness = np.mean(gray)

            # Calculate overall quality score
            quality_score = (
                face_area_ratio * 0.3  # Larger faces = better
                + (1 - center_distance) * 0.2  # Centered faces = better
                + min(encoding_strength / 1.2, 1.0) * 0.3  # Strong encodings = better
                +
                # Good lighting = better
                min(brightness / 128, 2 - brightness / 128) * 0.2
            )

            image_metrics.append(
                {
                    "path": image_path,
                    "encoding": encoding,
                    "quality_score": quality_score,
                    "face_area_ratio": face_area_ratio,
                    "brightness": brightness,
                    "center_distance": center_distance,
                    "encoding_strength": encoding_strength,
                }
            )

            print(f"✅ Quality: {quality_score:.3f}")

        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}...")
            continue

    if len(image_metrics) < target_count:
        print(
            f"{Fore.YELLOW}⚠️ Only {len(image_metrics)} valid images found{Style.RESET_ALL}"
        )
        return True

    print(f"\n🧠 Selecting {target_count} most diverse and high-quality images...")

    # Smart selection algorithm
    selected_images = []
    remaining_images = image_metrics.copy()

    # Step 1: Select the highest quality image as anchor
    remaining_images.sort(key=lambda x: x["quality_score"], reverse=True)
    selected_images.append(remaining_images.pop(0))
    anchor_name = selected_images[-1]["path"].name
    anchor_quality = selected_images[-1]["quality_score"]
    print(f"   1. {anchor_name} (quality: {anchor_quality:.3f}) [anchor]")

    # Step 2: Select remaining images based on diversity + quality
    for i in range(1, target_count):
        if not remaining_images:
            break

        best_candidate = None
        best_score = -1

        for candidate in remaining_images:
            # Calculate diversity score (distance from already selected images)
            min_distance = float("inf")
            for selected in selected_images:
                # Encoding similarity (lower = more similar)
                encoding_distance = np.linalg.norm(
                    candidate["encoding"] - selected["encoding"]
                )

                # Brightness difference (lighting diversity)
                brightness_diff = (
                    abs(candidate["brightness"] - selected["brightness"]) / 255
                )

                # Combined diversity
                diversity = encoding_distance * 0.7 + brightness_diff * 0.3
                min_distance = min(min_distance, diversity)

            # Combined score: diversity + quality
            combined_score = min_distance * 0.6 + candidate["quality_score"] * 0.4

            if combined_score > best_score:
                best_score = combined_score
                best_candidate = candidate

        if best_candidate:
            selected_images.append(best_candidate)
            remaining_images.remove(best_candidate)
            quality_str = f"quality: {best_candidate['quality_score']:.3f}"
            diversity_str = f"diversity: {best_score:.3f}"
            print(
                f"   {i+1}. {best_candidate['path'].name} ({quality_str}, {diversity_str})"
            )

    # Step 3: Backup non-selected images
    backup_dir = reference_dir / "backup_smart_selection"
    backup_dir.mkdir(exist_ok=True)

    non_selected = [img for img in image_metrics if img not in selected_images]

    print(f"\n📦 Moving {len(non_selected)} non-selected images to backup...")
    for img_data in non_selected:
        try:
            backup_path = backup_dir / img_data["path"].name
            img_data["path"].rename(backup_path)
            print(f"   📁 {img_data['path'].name} → backup_smart_selection/")
        except Exception as e:
            print(f"   ❌ Failed to move {img_data['path'].name}: {e}")

    # Step 4: Rename selected images sequentially
    print(f"\n🔄 Renaming {len(selected_images)} selected images sequentially...")
    for i, img_data in enumerate(selected_images):
        new_name = f"reference_{i:02d}.jpg"
        if img_data["path"].name != new_name:
            new_path = img_data["path"].parent / new_name
            try:
                img_data["path"].rename(new_path)
                print(f"   📝 {img_data['path'].name} → {new_name}")
            except Exception as e:
                print(f"   ❌ Failed to rename {img_data['path'].name}: {e}")

    print("\n✅ Smart selection complete!")
    print(f"   🎯 Selected: {len(selected_images)} high-quality, diverse images")
    print(f"   📦 Backed up: {len(non_selected)} images")
    improvement = len(image_metrics) / len(selected_images)
    print(f"   🔥 Performance improvement: ~{improvement:.1f}x faster")

    # Clear encodings cache to regenerate with selected images
    encodings_file = reference_dir / "encodings.pkl"
    if encodings_file.exists():
        encodings_file.unlink()
        print("🔄 Cleared encodings cache - will regenerate with selected images")

    return True


def regenerate_encodings(auto_select_count=None):
    """Regenerate face encodings from current reference images."""
    print(f"\n{Fore.CYAN}🔄 Regenerating face encodings...{Style.RESET_ALL}")

    # Check if we should auto-select optimal images first
    if auto_select_count:
        reference_dir = get_facial_recognition_param("reference_images_dir")
        reference_images = list(reference_dir.glob("reference_*.jpg"))

        if len(reference_images) > auto_select_count:
            print(
                f"📊 Found {len(reference_images)} images, auto-selecting "
                f"{auto_select_count} best ones..."
            )
            if not smart_select_reference_images(auto_select_count):
                print(
                    f"{Fore.YELLOW}⚠️ Smart selection failed, using all images{Style.RESET_ALL}"
                )

    # Use the efficient combined function
    return validate_and_generate_encodings()


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Facial Recognition Setup and Calibration"
    )
    parser.add_argument(
        "--capture",
        "-c",
        type=int,
        metavar="N",
        help="Capture N reference images manually (default: 10)",
    )
    parser.add_argument(
        "--live-capture",
        "-lc",
        type=int,
        metavar="N",
        help="Automatically capture N reference images from live feed (default: 20)",
    )
    parser.add_argument(
        "--test-live", "-tl", action="store_true", help="Test live facial recognition"
    )
    parser.add_argument(
        "--full-setup", "-f", action="store_true", help="Run complete setup process"
    )
    parser.add_argument(
        "--regenerate", "-r", action="store_true", help="Regenerate face encodings"
    )
    parser.add_argument(
        "--regenerate-optimized",
        "-ro",
        type=int,
        metavar="N",
        help="Regenerate encodings with auto-selection of N best images (default: 10)",
    )
    parser.add_argument(
        "--smart-select",
        "-s",
        type=int,
        metavar="N",
        help="Smart selection of N best reference images (default: 10)",
    )

    args = parser.parse_args()
    setup_logging()

    logging.info("🔧 Facial Recognition Setup and Calibration Tool")
    logging.info("=" * 50)

    # Check basic requirements
    if not check_dependencies():
        return 1

    if not check_camera():
        return 1

    # Handle specific commands
    if args.test_live:
        test_live_recognition()
        return 0

    if args.regenerate_optimized:
        count = args.regenerate_optimized
        if regenerate_encodings(auto_select_count=count):
            logging.info(
                f"✅ Encodings regenerated with auto-selection of {count} images"
            )
        else:
            logging.error("❌ Failed to regenerate optimized encodings")
        return 0

    if args.regenerate:
        # Ask user if they want auto-selection
        reference_dir = get_facial_recognition_param("reference_images_dir")
        reference_images = list(reference_dir.glob("reference_*.jpg"))

        if len(reference_images) > 10:
            print(f"📊 Found {len(reference_images)} reference images")
            response = (
                input("Auto-select 10 best images for optimal performance? (Y/n): ")
                .strip()
                .lower()
            )

            if response != "n":
                if regenerate_encodings(auto_select_count=10):
                    logging.info(
                        "✅ Encodings regenerated with auto-selection of 10 images"
                    )
                else:
                    logging.error("❌ Failed to regenerate optimized encodings")
            else:
                if regenerate_encodings():
                    logging.info("✅ Encodings regenerated with all images")
                else:
                    logging.error("❌ Failed to regenerate encodings")
        else:
            if regenerate_encodings():
                logging.info("✅ Encodings regenerated successfully")
            else:
                logging.error("❌ Failed to regenerate encodings")
        return 0

    if args.smart_select:
        if not enable_facial_recognition():
            return 1

        ref_dir = setup_reference_directory()
        if not ref_dir:
            return 1

        count = args.smart_select if args.smart_select > 0 else 10
        if smart_select_reference_images(count):
            logging.info("✅ Smart selection completed successfully")

            # Regenerate encodings with selected images
            if regenerate_encodings():
                logging.info("✅ Encodings regenerated with selected images")
            else:
                logging.error("❌ Failed to regenerate encodings")
        else:
            logging.error("❌ Smart selection failed")
        return 0

    # Live capture mode
    if args.live_capture:
        if not enable_facial_recognition():
            return 1

        ref_dir = setup_reference_directory()
        if not ref_dir:
            return 1

        num_images = args.live_capture
        captured = auto_capture_reference_images(ref_dir, num_images)

        if captured == 0:
            logging.error("❌ No images captured")
            return 1

        logging.info(f"✅ Auto-capture completed with {captured} images")
        return 0

    # Full setup or manual capture
    if not enable_facial_recognition():
        return 1

    ref_dir = setup_reference_directory()
    if not ref_dir:
        return 1

    if args.capture or args.full_setup:
        num_images = args.capture if args.capture else 10
        captured = capture_reference_images(ref_dir, num_images)

        if captured == 0:
            logging.error("❌ No images captured")
            return 1

    if args.full_setup:
        # Validate complete configuration
        errors = validate_config()
        if errors:
            logging.error("❌ Configuration validation failed:")
            for error in errors:
                logging.error(f"   - {error}")
            return 1

        logging.info("✅ Configuration validation passed")

        # Offer live test
        response = input("\nTest live recognition now? (y/N): ").strip().lower()
        if response == "y":
            test_live_recognition()

    # Default behavior: run live capture if no specific action was taken
    elif not any([args.capture, args.full_setup]):
        logging.info("🤖 No specific action provided - starting automatic live capture")
        logging.info("Use --help to see all available options")

        # No limit - capture until ESC
        captured = auto_capture_reference_images(ref_dir, num_images=None)

        if captured == 0:
            logging.error("❌ No images captured")
            return 1

        logging.info(f"✅ Auto-capture completed with {captured} images")

    logging.info("\n🎉 Setup completed successfully!")
    logging.info("Next steps:")
    logging.info("1. Test with: python3 face_detector.py --debug")
    logging.info("2. Monitor logs in: /tmp/face_detector.log")
    logging.info("3. Adjust config.py settings as needed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
