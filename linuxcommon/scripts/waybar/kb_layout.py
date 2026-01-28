#!/usr/bin/env python3
"""
Custom Waybar module to display keyboard layout variant
"""

import subprocess
import json


def get_current_layout():
    """Get the current keyboard layout and return a short display string"""
    try:
        # Get device info as JSON
        result = subprocess.run(
            ["hyprctl", "devices", "-j"], capture_output=True, text=True
        )

        if result.returncode != 0:
            return "⌨ ???"

        devices = json.loads(result.stdout)

        # Find the first keyboard device
        for keyboard in devices.get("keyboards", []):
            if keyboard.get("name"):
                active_keymap = keyboard.get("active_keymap", "")

                # Map layout descriptions to short display strings
                if "colemak" in active_keymap.lower():
                    return "⌨ CMK"
                elif "no dead keys" in active_keymap.lower():
                    return "⌨ SWE"
                else:
                    return "⌨ SWE"  # Default to Swedish

        return "⌨ ???"

    except Exception as e:
        return "⌨ ERR"


if __name__ == "__main__":
    print(get_current_layout())
