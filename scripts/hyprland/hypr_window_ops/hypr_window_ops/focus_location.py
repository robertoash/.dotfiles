#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys


def run_hyprctl(command):
    """Run a hyprctl command and return the parsed JSON output."""
    result = subprocess.run(["hyprctl"] + command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {' '.join(command)}: {result.stderr}")
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None


def get_clients():
    """Get all clients/windows."""
    return run_hyprctl(["clients", "-j"]) or []


def get_monitors():
    """Get all monitors."""
    return run_hyprctl(["monitors", "-j"]) or []


def focus_window(address):
    """Focus a window by address."""
    subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{address}"])


def get_active_window():
    """Get the active window information."""
    return run_hyprctl(["activewindow", "-j"])


def get_target_monitor_id(monitor_side):
    """
    Get the target monitor ID (0, 1, etc.) based on position (left or right).
    Identifies monitors by sorting them by x-coordinate.
    """
    monitors = get_monitors()
    if not monitors:
        print("No monitors detected!")
        return None

    # Sort monitors by x-coordinate
    sorted_monitors = sorted(monitors, key=lambda m: m.get("x", 0))

    # Find index of monitors in the sorted list
    if monitor_side == "left" and sorted_monitors:
        # Find the index of the leftmost monitor in the original list
        leftmost = sorted_monitors[0]
        for i, mon in enumerate(monitors):
            if mon.get("name") == leftmost.get("name"):
                return i  # This is the monitor ID (0, 1, etc.)
    elif monitor_side == "right" and len(sorted_monitors) > 1:
        # Find the index of the rightmost monitor in the original list
        rightmost = sorted_monitors[-1]
        for i, mon in enumerate(monitors):
            if mon.get("name") == rightmost.get("name"):
                return i  # This is the monitor ID (0, 1, etc.)
    elif monitor_side == "right" and len(sorted_monitors) == 1:
        # Only one monitor, treat it as both left and right
        return 0  # The only monitor has ID 0

    return None


def sort_windows_by_position(windows, monitor):
    """
    Sort windows taking monitor transform into account.
    This correctly handles rotated monitors.
    """
    if not windows:
        return []

    # Get monitor transform
    transform = monitor.get("transform", 0)

    # Check if monitor is rotated (1=90°, 3=270°)
    is_vertical = transform in [1, 3]

    # Sort windows by position
    if is_vertical:
        # For vertical monitors, sort by y first, then x
        windows.sort(key=lambda w: (w.get("at", [0, 0])[1], w.get("at", [0, 0])[0]))
    else:
        # For horizontal monitors, sort by x first, then y
        windows.sort(key=lambda w: (w.get("at", [0, 0])[0], w.get("at", [0, 0])[1]))

    return windows


def get_windows_by_location(monitor_side):
    """
    Get windows organized by their location (master, slave1, slave2, slave3)
    for a specific monitor.
    """
    clients = get_clients()
    if not clients:
        print("No windows found on any monitor")
        return {}

    # Get the target monitor ID
    target_monitor_id = get_target_monitor_id(monitor_side)
    if target_monitor_id is None:
        print(f"No {monitor_side} monitor found")
        return {}

    # Get all monitors to find transform info and active workspace
    monitors = get_monitors()
    target_monitor = (
        monitors[target_monitor_id] if target_monitor_id < len(monitors) else None
    )
    if not target_monitor:
        print(f"Error: Monitor with ID {target_monitor_id} not found")
        return {}

    # Get the active workspace ID for the target monitor
    active_workspace_id = target_monitor.get("activeWorkspace", {}).get("id")
    if active_workspace_id is None:
        print("Error: Could not determine active workspace for monitor")
        return {}

    # Get windows on the target monitor AND in the active workspace
    monitor_windows = [
        c
        for c in clients
        if c.get("monitor") == target_monitor_id
        and c.get("workspace", {}).get("id") == active_workspace_id
    ]

    if not monitor_windows:
        print(f"No windows found on {monitor_side} monitor in active workspace")
        return {}

    # Sort windows by position, accounting for monitor rotation
    monitor_windows = sort_windows_by_position(monitor_windows, target_monitor)

    # Create dictionary of window locations
    window_positions = {}

    # The first window is the master
    window_positions["master"] = monitor_windows[0]["address"]

    # Assign remaining windows to slave positions
    for i, window in enumerate(monitor_windows[1:], 1):
        position = f"slave{i}"
        if i <= 3:  # We only support up to slave3
            window_positions[position] = window["address"]

    return window_positions


def focus_by_location(monitor_side, position):
    """Focus a window at a specific location (master, slave1, etc.) on the specified monitor."""
    window_positions = get_windows_by_location(monitor_side)

    if not window_positions:
        print(f"No windows found on {monitor_side} monitor")
        return 1

    # If the exact position isn't available, use fallback logic
    if position not in window_positions:
        if position.startswith("slave"):
            # If any slave position is requested but not available

            # Try to find the highest available slave position
            available_slaves = sorted(
                [pos for pos in window_positions.keys() if pos.startswith("slave")]
            )

            if available_slaves:
                # Use the last (highest numbered) available slave
                fallback_position = available_slaves[-1]
                print(
                    f"Position {position} not found, focusing {fallback_position} instead"
                )
                target_address = window_positions[fallback_position]
            elif "master" in window_positions:
                # No slaves available, fall back to master
                print("No slave positions found, focusing master instead")
                target_address = window_positions["master"]
            else:
                print(
                    f"No window found at position {position} on {monitor_side} monitor"
                )
                return 1
        else:
            print(f"No window found at position {position} on {monitor_side} monitor")
            return 1
    else:
        target_address = window_positions[position]

    # Check if the target window is already focused
    active_window = get_active_window()
    if active_window and active_window.get("address") == target_address:
        # Already focused, do nothing
        return 0

    focus_window(target_address)
    return 0


def main():
    """Entry point for the focus_location functionality."""
    parser = argparse.ArgumentParser(
        description="""
Focus a window at a specific location (master, slave1, etc.) on a monitor.
This helps with quickly navigating between window positions in Hyprland.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "monitor_side",
        choices=["left", "right"],
        help="Which monitor to target (left or right)",
    )

    parser.add_argument(
        "position",
        choices=["master", "slave1", "slave2", "slave3"],
        help="Window position to focus (master, slave1, slave2, slave3)",
    )

    args = parser.parse_args()
    return focus_by_location(args.monitor_side, args.position)


if __name__ == "__main__":
    sys.exit(main())
