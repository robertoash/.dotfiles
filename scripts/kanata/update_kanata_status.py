#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Use a different file that should work with root permissions
STATUS_FILE = Path("/tmp/kanata_status.json")


def main():
    if len(sys.argv) != 2:
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode not in ["start-fresh", "set-to-plain", "set-to-nordic"]:
        sys.exit(1)

    # Handle start-fresh mode to initialize status file on boot
    if mode == "start-fresh":
        status = {
            "text": "MOD",
            "class": "normal",
            "tooltip": "Kanata: Nordic mode (home row mods active)",
        }
        STATUS_FILE.write_text(json.dumps(status))
        return

    # Handle set-to-plain mode - always set to plain state (idempotent)
    if mode == "set-to-plain":
        status = {
            "text": "NO-MODS",
            "class": "plain",
            "tooltip": "Kanata: Plain mode (no home row mods)",
        }
        STATUS_FILE.write_text(json.dumps(status))
        return

    # Handle set-to-nordic mode - always set to nordic state (idempotent)
    if mode == "set-to-nordic":
        status = {
            "text": "MOD",
            "class": "normal",
            "tooltip": "Kanata: Nordic mode (home row mods active)",
        }
        STATUS_FILE.write_text(json.dumps(status))
        return


if __name__ == "__main__":
    main()
