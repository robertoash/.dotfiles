#!/usr/bin/env python3
import json
import socket
import sys
from pathlib import Path

# Use a different file that should work with root permissions
STATUS_FILE = Path("/tmp/kanata_status.json")


def send_kanata_command(command):
    """Send a command to Kanata's TCP server using JSON format"""
    try:
        # Format the command as JSON as required by Kanata's TCP protocol
        json_command = json.dumps({"ChangeLayer": {"new": command.split()[1]}})

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)  # 1 second timeout
            sock.connect(("127.0.0.1", 9999))
            sock.sendall(json_command.encode("utf-8"))

            # Try to read the response
            response = sock.recv(1024).decode("utf-8")
            print(f"DEBUG: Received response: {response}", file=sys.stderr)

            sock.close()
            return True
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        print(f"DEBUG: Failed to send command '{command}': {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) != 2:
        sys.exit(1)

    mode = sys.argv[1].lower()
    if mode not in ["start-fresh", "toggle", "switch-to-json-state"]:
        sys.exit(1)

    # Handle start-fresh mode to initialize status file on boot
    if mode == "start-fresh":
        status = {
            "text": "NORM",
            "class": "normal",
            "tooltip": "Kanata: Nordic mode (home row mods active)",
        }
        STATUS_FILE.write_text(json.dumps(status))
        STATUS_FILE.chmod(0o666)  # World readable and writable
        return

    # Handle toggle mode - just toggle JSON state, no layer switching
    if mode == "toggle":
        current_status = {"class": "normal"}  # default
        try:
            if STATUS_FILE.exists():
                current_status = json.loads(STATUS_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Toggle to opposite mode
        if current_status.get("class") == "plain":
            new_class = "normal"
            text = "NORM"
            tooltip = "Kanata: Nordic mode (home row mods active)"
        else:
            new_class = "plain"
            text = "NOMODS"
            tooltip = "Kanata: Plain mode (no home row mods)"

        # Update JSON
        status = {"text": text, "class": new_class, "tooltip": tooltip}
        STATUS_FILE.write_text(json.dumps(status))
        STATUS_FILE.chmod(0o666)
        return

    # Handle switch-to-json-state mode - read JSON and switch layer accordingly
    if mode == "switch-to-json-state":
        # Small delay to ensure JSON file is written by previous toggle command
        import time

        time.sleep(0.1)

        current_status = {"class": "normal"}  # default to nordic
        try:
            if STATUS_FILE.exists():
                current_status = json.loads(STATUS_FILE.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Switch kanata layer based on JSON state
        if current_status.get("class") == "plain":
            target_layer = "almost_unchanged"
        else:
            target_layer = "nordic"

        # Debug output to stderr so we can see what's happening
        print(
            f"DEBUG: JSON class={current_status.get('class')}, switching to {target_layer}",
            file=sys.stderr,
        )

        # Send the layer switch command via TCP
        command = f"layer-switch {target_layer}"
        success = send_kanata_command(command)

        if success:
            print(f"DEBUG: Successfully sent command: {command}", file=sys.stderr)
        else:
            print(f"DEBUG: Failed to send command: {command}", file=sys.stderr)


if __name__ == "__main__":
    main()
