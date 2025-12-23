#!/usr/bin/env python3

"""Stash manager for handling monitor-specific stash workspaces."""

import sys

from . import window_manager


def get_active_monitor():
    """Get the currently active monitor information."""
    monitors = window_manager.run_hyprctl(["monitors", "-j"])
    if not monitors:
        return None
    
    for monitor in monitors:
        if monitor.get("focused", False):
            return monitor
    return None




def toggle_monitor_stash():
    """Toggle the stash workspace for the currently active monitor only.
    
    This is a simpler, more reliable alternative to toggle_both_stashes.
    It only affects the stash on the current monitor, avoiding race conditions.
    """
    # Get current monitor info
    monitor = get_active_monitor()
    if not monitor:
        print("Could not determine active monitor", file=sys.stderr)
        return 1
    
    monitor_name = monitor.get("name", "")
    monitor_desc = monitor.get("description", "")
    
    # Determine which stash belongs to this monitor
    if "HDMI-A-1" in monitor_name or "L32p-30" in monitor_desc:
        stash = "stash-right"
    elif "DP-1" in monitor_name or "P27u-20" in monitor_desc:
        stash = "stash-left"
    else:
        print(f"Unknown monitor: {monitor_name} ({monitor_desc}), cannot determine stash", file=sys.stderr)
        return 1
    
    # Toggle the stash for this monitor
    window_manager.toggle_special_workspace(stash)
    return 0


def move_to_monitor_stash(stash_name=None):
    """Toggle window between stash and regular workspace.

    If the window is in a special workspace (stash), moves it to the regular workspace.
    If the window is in a regular workspace, moves it to the stash.

    Args:
        stash_name: Optional specific stash name to use (e.g., "stash-left", "stash-right").
                   If not provided, automatically determines based on current monitor.
    """
    # Get active window to check current workspace
    active_window = window_manager.run_hyprctl(["activewindow", "-j"])
    if not active_window:
        print("No active window")
        return 1

    current_workspace_id = active_window.get("workspace", {}).get("id")

    # If already in a special workspace (negative ID), move to regular workspace
    if current_workspace_id and current_workspace_id < 0:
        monitor = get_active_monitor()
        if not monitor:
            print("Could not determine active monitor")
            return 1

        # Move to the active regular workspace on this monitor
        target_workspace = monitor.get("activeWorkspace", {}).get("id")
        window_manager.run_hyprctl_command(["dispatch", "movetoworkspacesilent", str(target_workspace)])
        print(f"Moved window from special workspace to workspace {target_workspace}")
        return 0

    # Otherwise, move to stash
    if stash_name:
        # Use the provided stash name
        stash = stash_name
    else:
        # Auto-detect based on current monitor
        monitor = get_active_monitor()
        if not monitor:
            print("Could not determine active monitor")
            return 1

        # Determine which stash to use based on monitor
        monitor_name = monitor.get("name", "")
        monitor_desc = monitor.get("description", "")

        # Map monitors to their stash workspaces
        if "HDMI-A-1" in monitor_name or "L32p-30" in monitor_desc:
            stash = "stash-right"
        elif "DP-1" in monitor_name or "P27u-20" in monitor_desc:
            stash = "stash-left"
        else:
            # Default fallback
            print(f"Unknown monitor: {monitor_name} ({monitor_desc}), using stash-left")
            stash = "stash-left"

    # Move the active window to the appropriate stash
    window_manager.run_hyprctl_command(["dispatch", "movetoworkspacesilent", f"special:{stash}"])

    print(f"Moved window to {stash}")
    return 0