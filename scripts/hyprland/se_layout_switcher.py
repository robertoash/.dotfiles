#!/usr/bin/env python3
"""
Hyprland Swedish Layout Switcher
Toggles between se layout with nodeadkeys and colemak variants
"""

import json
import subprocess
import sys


def run_command(cmd):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {cmd}")
            print(f"Error output: {result.stderr}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Exception running command: {cmd}")
        print(f"Exception: {e}")
        return None


def get_current_layout():
    """Get the current keyboard layout and variant"""
    try:
        # Get device info as JSON
        devices_json = run_command("hyprctl devices -j")
        if not devices_json:
            return None

        devices = json.loads(devices_json)

        # Find the first keyboard device
        for keyboard in devices.get("keyboards", []):
            if keyboard.get("name"):
                # Get the active keymap
                active_keymap = keyboard.get("active_keymap", "")
                return active_keymap

        return None
    except json.JSONDecodeError:
        print("Error parsing device JSON")
        return None
    except Exception as e:
        print(f"Error getting current layout: {e}")
        return None


def set_layout_variant(variant):
    """Set the keyboard layout variant"""
    cmd = f'hyprctl keyword input:kb_variant "{variant}"'
    result = run_command(cmd)
    return result is not None


def toggle_layout():
    """Toggle between se nodeadkeys and se colemak"""
    current_layout = get_current_layout()

    if current_layout is None:
        print("Could not determine current layout")
        return False

    print(f"Current layout: {current_layout}")

    # Check current variant and switch
    if "colemak" in current_layout.lower():
        # Switch to nodeadkeys
        print("Switching to Swedish (nodeadkeys)")
        success = set_layout_variant("nodeadkeys")
        if success:
            print("✓ Switched to Swedish (nodeadkeys)")
        else:
            print("✗ Failed to switch to nodeadkeys")
        return success
    else:
        # Switch to colemak (assuming current is nodeadkeys or default)
        print("Switching to Swedish (colemak)")
        success = set_layout_variant("colemak")
        if success:
            print("✓ Switched to Swedish (colemak)")
        else:
            print("✗ Failed to switch to colemak")
        return success


def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--nodeadkeys":
            print("Setting Swedish (nodeadkeys)")
            success = set_layout_variant("nodeadkeys")
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--colemak":
            print("Setting Swedish (colemak)")
            success = set_layout_variant("colemak")
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--status":
            current = get_current_layout()
            if current:
                print(f"Current layout: {current}")
            else:
                print("Could not determine current layout")
            sys.exit(0)
        elif sys.argv[1] in ["-h", "--help"]:
            print("Usage:")
            print("  python3 se_layout_switcher.py          # Toggle between variants")
            print("  python3 se_layout_switcher.py --nodeadkeys  # Set nodeadkeys")
            print("  python3 se_layout_switcher.py --colemak     # Set colemak")
            print("  python3 se_layout_switcher.py --status      # Show current layout")
            print("  python3 se_layout_switcher.py --help        # Show this help")
            sys.exit(0)

    # Default action: toggle
    success = toggle_layout()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
