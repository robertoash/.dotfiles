#!/usr/bin/env python3

from . import window_manager as wm


def get_active_monitor():
    """Get the currently focused monitor."""
    monitors = wm.run_hyprctl(["monitors", "-j"])
    if not monitors:
        return None

    for monitor in monitors:
        if monitor.get("focused"):
            return monitor
    return None


def get_windows_on_monitor(monitor_id):
    """
    Get all cycleable windows on a specific monitor.

    Filters out:
    - Pinned windows
    - Special workspaces (negative IDs)
    - Unmapped windows

    Includes both tiled and floating windows.
    Windows are sorted by position (top to bottom, left to right).
    """
    clients = wm.get_clients()
    if not clients:
        return []

    # Filter windows on the current monitor
    windows = [
        c for c in clients
        if c.get("monitor") == monitor_id
        and not c.get("pinned", False)  # Exclude pinned windows
        and c.get("mapped", True)  # Only mapped windows
        and c.get("workspace", {}).get("id", -1) >= 0  # Exclude special workspaces
    ]

    # Sort by position (top to bottom, left to right) for consistent ordering
    windows.sort(key=lambda w: (w.get("at", [0, 0])[1], w.get("at", [0, 0])[0]))

    return windows


def cycle_windows():
    """
    Cycle focus through windows on the current monitor.

    Cycles through all tiled and floating windows on the active monitor,
    excluding pinned windows and special workspaces.
    """
    active_window = wm.run_hyprctl(["activewindow", "-j"])
    active_monitor = get_active_monitor()

    if not active_monitor:
        return 1

    monitor_id = active_monitor["id"]
    windows = get_windows_on_monitor(monitor_id)

    if len(windows) <= 1:
        # Nothing to cycle
        return 0

    # Find current window index
    current_address = active_window.get("address") if active_window else None
    current_index = None

    for i, window in enumerate(windows):
        if window.get("address") == current_address:
            current_index = i
            break

    # Calculate next window index
    if current_index is not None:
        next_index = (current_index + 1) % len(windows)
    else:
        # If current window not found, just focus the first one
        next_index = 0

    next_window = windows[next_index]
    next_address = next_window.get("address")

    if next_address:
        wm.focus_window(next_address)

    return 0
