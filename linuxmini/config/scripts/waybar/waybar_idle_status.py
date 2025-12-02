#!/usr/bin/env python3
"""
Enhanced waybar status updater for idle detection system.
Shows detailed status with color coding:
- ⚫ (Black): Error conditions (MQTT unavailable, etc.)
- 🟡 (Yellow): Automatically marked as not idle by logic
- 🔴 (Red): Manual override is active
- ⚪ (White): Normal idle monitoring active
"""

import json
import subprocess
import time
from pathlib import Path


def is_hypridle_running():
    """Check if any hypridle process is running."""
    result = subprocess.run(["pgrep", "-x", "hypridle"], stdout=subprocess.PIPE)
    return result.returncode == 0


def get_in_office_status():
    """Get the in_office status from MQTT file."""
    status_file = Path("/tmp/mqtt/in_office_status")

    # Wait a moment for MQTT services to populate the file at startup
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            return status_file.read_text().strip()
        except FileNotFoundError:
            if attempt < max_attempts - 1:
                time.sleep(1)  # Wait 1 second and retry
            continue
    return None


def is_manual_override_active():
    """Check if manual override is active."""
    # Check MQTT file first (new method)
    mqtt_override_file = Path("/tmp/mqtt/manual_override_status")
    if mqtt_override_file.exists():
        try:
            content = mqtt_override_file.read_text().strip()
            return content == "active"
        except (FileNotFoundError, IOError):
            pass

    # Fall back to local file (old method)
    override_file = Path("/tmp/waybar/manual_override")
    return override_file.exists()


def determine_status():
    """Determine the appropriate status icon and tooltip."""
    hypridle_running = is_hypridle_running()
    in_office_status = get_in_office_status()
    manual_override = is_manual_override_active()

    # Priority 1: Manual override (Red)
    if manual_override:
        return (
            "🔴",
            "Manual override active - Idle detection disabled",
            "manual_override",
        )

    # Priority 2: Error conditions (Black)
    if not hypridle_running:
        return "⚫", "Error: Hypridle not running", "error"

    if in_office_status is None:
        return "⚫", "Error: MQTT status unavailable", "error"

    # Priority 3: Automatically marked as active (Yellow)
    if in_office_status == "on":
        return "🟡", "Automatically marked as active (not idle)", "auto_active"

    # Priority 4: Normal idle monitoring (White)
    return "⚪", "Idle monitoring active", "idle_monitoring"


def update_waybar_status():
    """Update the waybar status files."""
    waybar_dir = Path("/tmp/waybar")
    waybar_dir.mkdir(parents=True, exist_ok=True)

    icon, tooltip, status_class = determine_status()

    # Update simple status file used by current waybar config
    status_file = waybar_dir / "hypridle_status.json"
    status_file.write_text(icon)

    # Create detailed JSON status file
    idle_status_file = waybar_dir / "idle_status.json"
    status_data = {
        "text": icon,
        "tooltip": tooltip,
        "class": status_class,
        "alt": status_class,
    }
    idle_status_file.write_text(json.dumps(status_data, indent=2))

    print(f"Waybar status updated: {tooltip}")


def main():
    """Main function."""
    update_waybar_status()


if __name__ == "__main__":
    main()
