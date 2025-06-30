#!/usr/bin/env python3

import time
from datetime import datetime
from pathlib import Path

# Files to monitor with descriptions
files_to_monitor = {
    "/tmp/mqtt/linux_mini_status": "User Activity Status",
    "/tmp/mqtt/idle_detection_status": "Idle Detection Status",
    "/tmp/mqtt/face_presence": "Face Detection Status",
    "/tmp/mqtt/in_office_status": "Office Presence Status",
    "/tmp/mqtt/manual_override_status": "Manual Override Status",
}

# Additional control files to monitor
control_files = {
    "/tmp/idle_simple_lock_exit": "Lock Exit Flag",
    "/tmp/in_office_monitor_exit": "Office Monitor Exit Flag",
    "/tmp/face_detector.log": "Face Detector Log (last 2 lines)",
    "/tmp/idle_simple_lock.log": "Lock Script Log (last 2 lines)",
}

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


def read_log_tail(path, lines=2):
    """Read last N lines from a log file."""
    try:
        with open(path, "r") as f:
            all_lines = f.readlines()
            return "".join(all_lines[-lines:]).strip() if all_lines else ""
    except Exception:
        return None


def check_file_exists(path):
    """Check if file exists."""
    return Path(path).exists()


def log_event(message, level="INFO"):
    """Log an event with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {level}: {message}")


def analyze_system_state():
    """Analyze and describe the current system state."""
    user_status = read_file("/tmp/mqtt/linux_mini_status")
    idle_status = read_file("/tmp/mqtt/idle_detection_status")
    face_status = read_file("/tmp/mqtt/face_presence")
    office_status = read_file("/tmp/mqtt/in_office_status")

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
        f"Monitoring {len(files_to_monitor)} status files and {len(control_files)} control files",
        "SYSTEM",
    )

    # Initialize previous values
    for path in files_to_monitor:
        previous_values[path] = read_file(path)
    for path in control_files:
        if path.endswith(".log"):
            previous_log_sizes[path] = (
                Path(path).stat().st_size if Path(path).exists() else 0
            )
        else:
            previous_values[path] = check_file_exists(path)

    # Print initial state
    log_event("Initial system state:", "STATE")
    for path, description in files_to_monitor.items():
        value = previous_values[path]
        log_event(f"  {description}: {value}", "STATE")

    log_event(f"System State Summary: {analyze_system_state()}", "STATE")
    log_event("--- Starting continuous monitoring ---", "SYSTEM")

    try:
        while True:
            changes_detected = False

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
                if path.endswith(".log"):
                    # Monitor log files for new content
                    if Path(path).exists():
                        current_size = Path(path).stat().st_size
                        previous_size = previous_log_sizes.get(path, 0)
                        if current_size > previous_size:
                            changes_detected = True
                            new_content = read_log_tail(path, 3)
                            if new_content:
                                log_event(f"{description} NEW ENTRIES:", "LOG")
                                for line in new_content.split("\n"):
                                    if line.strip():
                                        log_event(f"  {line}", "LOG")
                            previous_log_sizes[path] = current_size
                else:
                    # Monitor flag files
                    current_exists = check_file_exists(path)
                    previous_exists = previous_values.get(path, False)

                    if current_exists != previous_exists:
                        changes_detected = True
                        if current_exists:
                            log_event(f"{description} CREATED", "FLAG")
                        else:
                            log_event(f"{description} DELETED", "FLAG")
                        previous_values[path] = current_exists

            # If any changes detected, show current system state
            if changes_detected:
                state_summary = analyze_system_state()
                log_event(f"Current State: {state_summary}", "STATE")
                log_event("---", "STATE")

            time.sleep(0.5)  # Check every 500ms for faster response

    except KeyboardInterrupt:
        log_event("=== DEBUG LOGGER STOPPED BY USER ===", "SYSTEM")


if __name__ == "__main__":
    monitor_files()
