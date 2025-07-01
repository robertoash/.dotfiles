#!/usr/bin/env python3

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import centralized configuration
from config import (  # noqa: E402
    CONTROL_FILES,
    STATUS_FILES,
    get_all_log_files,
    get_check_interval,
)

# Files to monitor with descriptions
files_to_monitor = {
    str(STATUS_FILES["linux_mini_status"]): "User Activity Status",
    str(STATUS_FILES["idle_detection_status"]): "Idle Detection Status",
    str(STATUS_FILES["face_presence"]): "Face Detection Status",
    str(STATUS_FILES["in_office_status"]): "Office Presence Status",
    str(STATUS_FILES["manual_override_status"]): "Manual Override Status",
}

# Additional control files to monitor (non-log files)
control_files = {
    str(CONTROL_FILES["idle_simple_lock_exit"]): "Lock Exit Flag",
    str(CONTROL_FILES["in_office_monitor_exit"]): "Office Monitor Exit Flag",
}

# Log files to monitor separately
log_files = {}
for log_file in get_all_log_files():
    log_files[str(log_file)] = log_file.name

# Track previous values to detect changes
previous_values = {}
previous_log_sizes = {}


def read_file(path):
    """Read file content safely."""
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return None


def read_log_tail(path, lines=3):
    """Read last N lines from a log file."""
    try:
        with open(path, "r") as f:
            all_lines = f.readlines()
            return [line.strip() for line in all_lines[-lines:] if line.strip()]
    except Exception:
        return []


def check_file_exists(path):
    """Check if file exists."""
    return Path(path).exists()


def log_event(message, level="INFO"):
    """Log an event with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {level}: {message}")


def analyze_system_state():
    """Analyze and describe the current system state."""
    user_status = read_file(str(STATUS_FILES["linux_mini_status"]))
    idle_status = read_file(str(STATUS_FILES["idle_detection_status"]))
    face_status = read_file(str(STATUS_FILES["face_presence"]))
    office_status = read_file(str(STATUS_FILES["in_office_status"]))

    state_description = []

    if user_status == "active":
        state_description.append("User is ACTIVE")
    elif user_status == "inactive":
        state_description.append("User is INACTIVE")

    if idle_status == "in_progress":
        state_description.append("Idle detection is RUNNING")
    elif idle_status == "inactive":
        state_description.append("Idle detection is STOPPED")

    if face_status == "detected":
        state_description.append("Face is DETECTED")
    elif face_status == "not_detected":
        state_description.append("Face is NOT DETECTED")

    if office_status == "on":
        state_description.append("Office presence is ON")
    elif office_status == "off":
        state_description.append("Office presence is OFF")

    return " | ".join(state_description)


def monitor_files():
    """Monitor all files for changes."""
    log_event("=== IDLE MANAGEMENT DEBUG LOGGER STARTED ===", "SYSTEM")
    log_event(
        f"Monitoring {len(files_to_monitor)} status files, "
        f"{len(control_files)} control files, and {len(log_files)} log files",
        "SYSTEM",
    )

    # Initialize previous values
    for path in files_to_monitor:
        previous_values[path] = read_file(path)
    for path in control_files:
        previous_values[path] = check_file_exists(path)
    for path in log_files:
        previous_log_sizes[path] = (
            Path(path).stat().st_size if Path(path).exists() else 0
        )

    # Print initial state
    log_event("Initial system state:", "STATE")
    for path, description in files_to_monitor.items():
        value = previous_values[path]
        log_event(f"  {description}: {value}", "STATE")

    log_event(f"System State Summary: {analyze_system_state()}", "STATE")
    log_event("--- Starting continuous monitoring ---", "SYSTEM")

    # Get monitoring interval from config
    check_interval = get_check_interval("debug_monitoring")

    try:
        while True:
            changes_detected = False
            log_changes = {}  # Collect log changes to print at the end

            # Monitor status files
            for path, description in files_to_monitor.items():
                current_value = read_file(path)
                previous_value = previous_values.get(path)

                if current_value != previous_value:
                    changes_detected = True
                    if previous_value is None:
                        log_event(
                            f"{description} FILE CREATED: '{current_value}'", "CHANGE"
                        )
                    elif current_value is None:
                        log_event(
                            f"{description} FILE DELETED (was: '{previous_value}')",
                            "CHANGE",
                        )
                    else:
                        log_event(
                            f"{description} CHANGED: '{previous_value}' → '{current_value}'",
                            "CHANGE",
                        )
                    previous_values[path] = current_value

            # Monitor control files (flags)
            for path, description in control_files.items():
                current_exists = check_file_exists(path)
                previous_exists = previous_values.get(path, False)

                if current_exists != previous_exists:
                    changes_detected = True
                    if current_exists:
                        log_event(f"{description} CREATED", "FLAG")
                    else:
                        log_event(f"{description} DELETED", "FLAG")
                    previous_values[path] = current_exists

            # Monitor log files for new content (collect changes, don't print yet)
            for path, log_name in log_files.items():
                if Path(path).exists():
                    current_size = Path(path).stat().st_size
                    previous_size = previous_log_sizes.get(path, 0)
                    if current_size > previous_size:
                        changes_detected = True
                        new_lines = read_log_tail(path, 5)  # Get more lines for context
                        if new_lines:
                            log_changes[log_name] = new_lines
                        previous_log_sizes[path] = current_size

            # If any changes detected, show current system state first
            if changes_detected:
                state_summary = analyze_system_state()
                log_event(f"Current State: {state_summary}", "STATE")

                # Now print log changes in separate groups
                if log_changes:
                    log_event("--- Log Updates ---", "LOGS")
                    for log_name, lines in log_changes.items():
                        log_event(f"{log_name}:", "LOGS")
                        for line in lines:
                            print(f"    {line}")  # Print without timestamp wrapper
                    log_event("--- End Log Updates ---", "LOGS")

                log_event("---", "STATE")

            time.sleep(check_interval)  # Use interval from config

    except KeyboardInterrupt:
        log_event("=== DEBUG LOGGER STOPPED BY USER ===", "SYSTEM")


if __name__ == "__main__":
    monitor_files()
