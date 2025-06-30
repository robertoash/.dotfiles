#!/usr/bin/env python3

from pathlib import Path


def cleanup_stale_flags():
    """Clean up any stale exit flags from previous sessions."""
    import glob

    # Updated exit flag patterns for simplified system
    exit_flag_patterns = [
        "/tmp/*_exit",
        "/tmp/*exit*",
        "/tmp/face_presence_coordinator_exit",  # Legacy flag
        "/tmp/continuous_face_monitor_exit",  # Disabled - face detection unplugged
        "/tmp/office_status_handler_exit",  # Disabled - using simple idle management
        "/tmp/in_office_monitor_exit",  # Current simplified system
    ]

    # Also explicitly clean up critical files
    explicit_cleanup_files = [
        "/tmp/in_office_monitor_exit",
        "/tmp/idle_simple_lock_exit",
    ]

    for pattern in exit_flag_patterns:
        for flag_file in glob.glob(pattern):
            try:
                Path(flag_file).unlink()
                print(f"Cleaned up stale exit flag: {flag_file}")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Warning: Could not clean up {flag_file}: {e}")

    # Explicitly clean up critical files with full paths
    for flag_file in explicit_cleanup_files:
        try:
            full_path = Path(flag_file).resolve()
            full_path.unlink(missing_ok=True)
            print(f"Explicitly cleaned up: {full_path}")
        except Exception as e:
            print(f"Warning: Could not clean up {flag_file}: {e}")


def init_status_files():
    """Initialize all status files needed by the simplified presence detection system."""

    # First, clean up any stale exit flags
    cleanup_stale_flags()

    # Create mqtt directory
    mqtt_dir = Path("/tmp/mqtt")
    mqtt_dir.mkdir(parents=True, exist_ok=True)

    # Initialize all status files with proper default values
    status_files = {
        "linux_mini_status": "active",  # Linux mini is active on boot
        "idle_detection_status": "inactive",  # Idle detection is not running on boot
        # "face_presence": "not_detected",  # Disabled - face detection unplugged
        "in_office_status": "on",  # Default to in office on boot
    }

    for filename, default_value in status_files.items():
        status_file = mqtt_dir / filename
        status_file.write_text(default_value)
        print(f"Initialized {status_file} = {default_value}")


if __name__ == "__main__":
    init_status_files()
    print("All simplified presence detection status files initialized successfully")
