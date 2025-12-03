#!/usr/bin/env python3

import argparse
import sys

from . import window_manager


def focus_window(address):
    """Focus a window by address."""
    window_manager.run_hyprctl_command(
        ["dispatch", "focuswindow", f"address:{address}"]
    )


def get_active_window():
    """Get the active window information."""
    return window_manager.run_hyprctl(["activewindow", "-j"])


def get_clients():
    """Get all clients/windows."""
    return window_manager.get_clients()


def get_monitors():
    """Get all monitors."""
    return window_manager.run_hyprctl(["monitors", "-j"]) or []


def get_target_monitor_id(monitor_side):
    """
    Get the target monitor ID based on position (left or right).
    Uses hyprctl to get monitor data directly.
    """
    # Get monitor data directly from hyprctl
    monitors = window_manager.run_hyprctl(["monitors", "-j"])
    if not monitors:
        print("No monitors detected!")
        return None

    if len(monitors) == 1:
        # Only one monitor, treat it as both left and right
        return monitors[0]["id"]

    # Sort monitors by x-coordinate
    sorted_monitors = sorted(monitors, key=lambda m: m.get("x", 0))

    # For left monitor, get the one with smallest x
    # For right monitor, get the one with largest x
    if monitor_side == "left":
        return sorted_monitors[0]["id"]
    else:  # right
        return sorted_monitors[-1]["id"]


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

    # Get monitor data directly from hyprctl
    monitors = window_manager.run_hyprctl(["monitors", "-j"])
    target_monitor = next(
        (m for m in monitors if m.get("id") == target_monitor_id), None
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
