#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

# Use a different file that should work with root permissions
STATUS_FILE = Path("/tmp/kanata_status.json")


def main():
    if len(sys.argv) != 2:
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode not in ["nordic", "plain"]:
        sys.exit(1)

    # Update waybar status
    if mode == "plain":
        status = {
            "text": "NOMODS",
            "class": "plain",
            "tooltip": "Kanata: Plain mode (no home row mods)",
        }
    else:
        status = {
            "text": "NORM",
            "class": "normal",
            "tooltip": "Kanata: Nordic mode (home row mods active)",
        }

    # Write file with proper permissions
    STATUS_FILE.write_text(json.dumps(status))
    STATUS_FILE.chmod(0o666)  # World readable and writable

    # Send notification
    icon = "⌨"
    if mode == "plain":
        title = f"{icon} PLAIN Mode"
        message = "Kanata: Plain mode activated\nHome row mods disabled"
    else:
        title = f"{icon} NORDIC Mode"
        message = "Kanata: Nordic mode activated\nHome row mods enabled"

    try:
        subprocess.run(
            ["notify-send", "-i", "keyboard", "-a", "Kanata", title, message],
            capture_output=True,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        pass


if __name__ == "__main__":
    main()
