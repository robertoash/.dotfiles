#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

# Status file location
STATUS_FILE = Path("/tmp/kanata_status.json")


def get_current_status():
    """Read current kanata status from JSON file"""
    try:
        if STATUS_FILE.exists():
            data = json.loads(STATUS_FILE.read_text())
            return data.get("class", "normal")
        else:
            # Default to normal if file doesn't exist
            return "normal"
    except (json.JSONDecodeError, OSError):
        return "normal"


def send_kanata_command(command):
    """Send a command to kanata via kanata_cmd_client"""
    try:
        # Try to send command to kanata - this requires kanata_cmd_client to be available
        subprocess.run(
            ["kanata_cmd_client", command], check=True, capture_output=True, text=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # If kanata_cmd_client fails or doesn't exist, continue anyway
        # The status file update will still work for waybar display
        return False


def write_status_safely(status_data):
    """Write status to file"""
    try:
        STATUS_FILE.write_text(json.dumps(status_data))
        return True
    except (PermissionError, OSError) as e:
        print(f"Error writing status file: {e}")
        return False


def toggle_mode():
    """Toggle between nordic and plain modes"""
    current_status = get_current_status()

    if current_status == "normal":
        # Switch to plain mode
        # Update status file
        status = {
            "text": "NOMODS",
            "class": "plain",
            "tooltip": "Kanata: Plain mode (no home row mods)",
        }
        write_status_safely(status)

        # Send layer switch command to kanata
        send_kanata_command("(layer-switch almost_unchanged)")

    else:  # current_status == "plain" or any other state
        # Switch to nordic mode
        # Update status file
        status = {
            "text": "NORM",
            "class": "normal",
            "tooltip": "Kanata: Nordic mode (home row mods active)",
        }
        write_status_safely(status)

        # Send layer switch command to kanata
        send_kanata_command("(layer-switch nordic)")


def main():
    """Main function to handle toggle"""
    toggle_mode()


if __name__ == "__main__":
    main()
