#!/usr/bin/env python3

"""Waybar module to show special workspace indicators."""

import json
import os
import subprocess
import sys


def get_current_monitor_side():
    """Determine which monitor side (left/right) this waybar instance is on."""
    # Check if Waybar provides output name via environment variable
    waybar_output = os.environ.get("WAYBAR_OUTPUT_NAME", "")

    if not waybar_output:
        return "error"  # Signal that detection failed

    try:
        result = subprocess.run(
            ["hyprctl", "monitors", "-j"],
            capture_output=True,
            text=True,
            check=True
        )
        monitors = json.loads(result.stdout)

        # Match by monitor name from WAYBAR_OUTPUT_NAME
        for monitor in monitors:
            monitor_name = monitor.get("name", "")
            monitor_desc = monitor.get("description", "")

            if waybar_output == monitor_name:
                if "L32p-30" in monitor_desc:
                    return "right"
                elif "P27u-20" in monitor_desc:
                    return "left"

        return "left"  # Default if no match
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return "left"


def get_active_special_workspace(monitor_side):
    """Get the active special workspace for this monitor.

    Args:
        monitor_side: "left" or "right" indicating which monitor

    Returns:
        The active special workspace name or None
    """
    try:
        result = subprocess.run(
            ["hyprctl", "monitors", "-j"],
            capture_output=True,
            text=True,
            check=True
        )
        monitors = json.loads(result.stdout)

        # Find the monitor for this side
        for monitor in monitors:
            monitor_desc = monitor.get("description", "")

            # Match monitor by description
            is_target_monitor = False
            if monitor_side == "right" and "L32p-30" in monitor_desc:
                is_target_monitor = True
            elif monitor_side == "left" and "P27u-20" in monitor_desc:
                is_target_monitor = True

            if is_target_monitor:
                # Check if a special workspace is active
                special_ws = monitor.get("specialWorkspace", {})
                if special_ws and special_ws.get("name"):
                    return special_ws.get("name")

        return None
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None


def get_special_workspace_counts(monitor_side):
    """Get count of windows in each special workspace for this monitor.

    Args:
        monitor_side: "left" or "right" indicating which monitor
    """
    try:
        result = subprocess.run(
            ["hyprctl", "clients", "-j"],
            capture_output=True,
            text=True,
            check=True
        )
        clients = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {"stash": 0, "secure": 0, "full": 0}

    counts = {"stash": 0, "secure": 0, "full": 0}

    for client in clients:
        workspace_name = client.get("workspace", {}).get("name", "")

        # Only count windows in THIS monitor's special workspaces
        if workspace_name == f"special:stash-{monitor_side}":
            counts["stash"] += 1
        elif workspace_name == f"special:secure-{monitor_side}":
            counts["secure"] += 1
        elif workspace_name == f"special:full-{monitor_side}":
            counts["full"] += 1

    return counts


def main():
    """Generate waybar output."""
    # Check if monitor side was passed as argument, otherwise detect it
    if len(sys.argv) > 1:
        monitor_side = sys.argv[1]
    else:
        monitor_side = get_current_monitor_side()

    # If detection failed, show error
    if monitor_side == "error":
        print(json.dumps({
            "text": " ERR ",
            "tooltip": "WAYBAR_OUTPUT_NAME not set",
            "class": "error"
        }))
        return

    counts = get_special_workspace_counts(monitor_side)
    active_workspace = get_active_special_workspace(monitor_side)

    # Determine which workspace is active
    active_ws = None
    if active_workspace == f"special:stash-{monitor_side}":
        active_ws = "stash"
    elif active_workspace == f"special:secure-{monitor_side}":
        active_ws = "secure"
    elif active_workspace == f"special:full-{monitor_side}":
        active_ws = "full"

    # If all are empty AND we're not in a special workspace, show just a black circle
    if all(count == 0 for count in counts.values()) and not active_ws:
        print(json.dumps({
            "text": " ⚫ ",
            "tooltip": "All special workspaces empty",
            "class": "empty"
        }))
        return

    # Build indicator text
    indicators = []
    tooltip_lines = []
    css_class = "has-windows"

    # Stash
    if active_ws == "stash":
        indicators.append("STASH 🟢")
        tooltip_lines.append(f"Stash: {counts['stash']} window(s) [ACTIVE]")
        css_class = "active-in"
    elif counts["stash"] > 0:
        indicators.append("S 🟠")
        tooltip_lines.append(f"Stash: {counts['stash']} window(s)")
    else:
        indicators.append("S ⚫")

    # Secure
    if active_ws == "secure":
        indicators.append("SECURE 🟢")
        tooltip_lines.append(f"Secure: {counts['secure']} window(s) [ACTIVE]")
        css_class = "active-in"
    elif counts["secure"] > 0:
        indicators.append("X 🟠")
        tooltip_lines.append(f"Secure: {counts['secure']} window(s)")
    else:
        indicators.append("X ⚫")

    # Full
    if active_ws == "full":
        indicators.append("FULL 🟢")
        tooltip_lines.append(f"Full: {counts['full']} window(s) [ACTIVE]")
        css_class = "active-in"
    elif counts["full"] > 0:
        indicators.append("F 🟠")
        tooltip_lines.append(f"Full: {counts['full']} window(s)")
    else:
        indicators.append("F ⚫")

    text = " " + " ".join(indicators) + " "
    tooltip = "\n".join(tooltip_lines) if tooltip_lines else "All special workspaces empty"

    print(json.dumps({
        "text": text,
        "tooltip": tooltip,
        "class": css_class
    }))


if __name__ == "__main__":
    main()
