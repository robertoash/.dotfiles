#!/usr/bin/env python3

"""
Centralized configuration for the Enhanced Idle Management System.

This file contains all configuration options used across the idle management scripts.
Modify values here to customize the behavior of the entire system.
"""

from pathlib import Path

# =============================================================================
# BASE DIRECTORIES
# =============================================================================

# Base directory for temporary files
TMP_DIR = Path("/tmp")

# MQTT status files directory
MQTT_DIR = TMP_DIR / "mqtt"

# REMOVED: OPENCV_CASCADE_DIR - no longer needed with MediaPipe + Motion

# Scripts directory
SCRIPTS_DIR = Path("/home/rash/.config/scripts")
IDLE_MANAGEMENT_DIR = SCRIPTS_DIR / "hyprland" / "idle_management"

# =============================================================================
# LOG FILES
# =============================================================================

LOG_FILES = {
    "face_detector": TMP_DIR / "face_detector.log",
    "idle_simple_lock": TMP_DIR / "idle_simple_lock.log",
    "idle_simple_dpms": TMP_DIR / "idle_simple_dpms.log",
    "idle_simple_resume": TMP_DIR / "idle_simple_resume.log",
    "in_office_monitor": TMP_DIR / "in_office_monitor.log",
    "activity_status_reporter": TMP_DIR / "mini_status_debug.log",
    "webcam_status": None,  # Uses logging_utils, no separate log file
}

# =============================================================================
# STATUS FILES (MQTT)
# =============================================================================

STATUS_FILES = {
    "linux_mini_status": MQTT_DIR / "linux_mini_status",
    "idle_detection_status": MQTT_DIR / "idle_detection_status",
    "face_presence": MQTT_DIR / "face_presence",
    "in_office_status": MQTT_DIR / "in_office_status",
    "linux_webcam_status": MQTT_DIR / "linux_webcam_status",
    "manual_override_status": MQTT_DIR / "manual_override_status",
}

# Default values for status files
STATUS_FILE_DEFAULTS = {
    "linux_mini_status": "active",
    "idle_detection_status": "inactive",
    "face_presence": "not_detected",
    "in_office_status": "on",
    "linux_webcam_status": "inactive",
    "manual_override_status": "inactive",
}

# =============================================================================
# CONTROL FILES (FLAGS)
# =============================================================================

CONTROL_FILES = {
    "idle_simple_lock_exit": TMP_DIR / "idle_simple_lock_exit",
    "in_office_monitor_exit": TMP_DIR / "in_office_monitor_exit",
    "in_office_monitor_pid": TMP_DIR / "in_office_monitor.pid",
}

# =============================================================================
# DEVICE FILES
# =============================================================================

DEVICE_FILES = {
    "webcam": Path("/dev/video0"),
}

# =============================================================================
# EXTERNAL SCRIPTS
# =============================================================================

EXTERNAL_SCRIPTS = {
    "activity_status_reporter": IDLE_MANAGEMENT_DIR / "activity_status_reporter.py",
}

# =============================================================================
# REMOVED: CASCADE FILES (No longer needed - using MediaPipe + Motion)
# =============================================================================
# Simplified detection system now uses only MediaPipe and motion detection

# =============================================================================
# TIMING CONFIGURATION
# =============================================================================

# Check intervals (in seconds)
CHECK_INTERVALS = {
    "lock_monitoring": 1,  # How often to check for office status changes during lock monitoring
    "dpms_monitoring": 1,  # How often to check for office status changes during DPMS monitoring
    "office_monitoring": 1,  # How often to check for office status changes in continuous monitoring
    "webcam_polling": 2,  # How often to poll webcam status when active
    "debug_monitoring": 0.5,  # How often to check for file changes in debug mode
}

# Face detection timeouts (in seconds)
FACE_DETECTION = {
    "initial_window": 5,  # Initial detection window duration
    "max_duration": 10,  # Maximum detection window duration
    "monitoring_interval": 60,  # How often to re-check presence during continuous monitoring
    "quick_check_duration": 3,  # Duration for quick presence checks during monitoring
}

# Resume delays (in seconds)
RESUME_DELAYS = {
    "exit_flag_cleanup": 2,  # How long to wait before cleaning up exit flags
}

# =============================================================================
# DETECTION PARAMETERS
# =============================================================================

# Optimized detection parameters (MediaPipe + Motion only)
DETECTION_PARAMS = {
    "threshold": 0.5,  # 50% threshold for presence detection
    "motion_min_area": 200,  # Min area for motion detection (reduced for phone usage)
    # MediaPipe parameters
    "mediapipe_enabled": True,  # Enable MediaPipe face mesh detection
    "mediapipe_min_detection_confidence": 0.5,  # MediaPipe detection confidence
    "mediapipe_min_tracking_confidence": 0.5,  # MediaPipe tracking confidence
}

# =============================================================================
# SYSTEM COMMANDS
# =============================================================================

SYSTEM_COMMANDS = {
    "hyprlock": ["hyprlock"],
    "hyprctl_dpms_on": ["hyprctl", "dispatch", "dpms", "on"],
    "hyprctl_dpms_off": ["hyprctl", "dispatch", "dpms", "off"],
    "pidof_hyprlock": ["pidof", "hyprlock"],
    "lsof_webcam": ["lsof"],  # Will append device path
    "inotifywait_webcam": ["inotifywait", "-e", "open"],  # Will append device path
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING_CONFIG = {
    "format": "%(asctime)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "level_info": "INFO",
    "level_debug": "DEBUG",
    "level_error": "ERROR",
}

# =============================================================================
# WEBCAM MONITORING
# =============================================================================

WEBCAM_CONFIG = {
    "excluded_processes": [
        "face_detector"
    ],  # Processes to exclude from webcam usage detection
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_log_file(script_name):
    """Get the log file path for a given script."""
    return LOG_FILES.get(script_name)


def get_status_file(status_name):
    """Get the status file path for a given status."""
    return STATUS_FILES.get(status_name)


def get_status_default(status_name):
    """Get the default value for a given status."""
    return STATUS_FILE_DEFAULTS.get(status_name)


def get_control_file(control_name):
    """Get the control file path for a given control."""
    return CONTROL_FILES.get(control_name)


# REMOVED: get_cascade_file function - no longer needed with MediaPipe + Motion


def get_check_interval(interval_name):
    """Get the check interval for a given operation."""
    return CHECK_INTERVALS.get(interval_name, 1)


def get_detection_param(param_name):
    """Get a detection parameter."""
    return DETECTION_PARAMS.get(param_name)


def get_system_command(command_name):
    """Get a system command."""
    return SYSTEM_COMMANDS.get(command_name, [])


def ensure_directories():
    """Ensure all required directories exist."""
    directories = [MQTT_DIR, TMP_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def get_all_status_files():
    """Get all status file paths as a list."""
    return list(STATUS_FILES.values())


def get_all_control_files():
    """Get all control file paths as a list."""
    return list(CONTROL_FILES.values())


def get_all_log_files():
    """Get all log file paths as a list (excluding None values)."""
    return [path for path in LOG_FILES.values() if path is not None]


# =============================================================================
# VALIDATION
# =============================================================================


def validate_config():
    """Validate that critical configuration is correct."""
    errors = []

    # Check that webcam device exists
    webcam_device = DEVICE_FILES["webcam"]
    if not webcam_device.exists():
        errors.append(f"Webcam device not found: {webcam_device}")

    # Check that scripts directory exists
    if not IDLE_MANAGEMENT_DIR.exists():
        errors.append(f"Scripts directory not found: {IDLE_MANAGEMENT_DIR}")

    return errors


if __name__ == "__main__":
    """Run configuration validation when executed directly."""
    print("Validating idle management configuration...")

    ensure_directories()
    print(f"✓ Created directories: {MQTT_DIR}, {TMP_DIR}")

    errors = validate_config()
    if errors:
        print("\n❌ Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("✓ Configuration validation passed")

    print("\nConfiguration summary:")
    print(f"  Status files: {len(STATUS_FILES)}")
    print(f"  Control files: {len(CONTROL_FILES)}")
    print(f"  Log files: {len([f for f in LOG_FILES.values() if f])}")
    print("  Detection methods: MediaPipe + Motion")
    print(f"  Check intervals: {len(CHECK_INTERVALS)}")
