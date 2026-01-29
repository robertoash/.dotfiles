#!/usr/bin/env python3

"""Stash manager for handling monitor-specific stash workspaces."""

import subprocess
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




def get_monitor_workspace(monitor, workspace_type="stash"):
    """Get the appropriate special workspace for a monitor.

    Args:
        monitor: Monitor info dict from hyprctl
        workspace_type: Type of workspace ("stash", "secure", or "full")

    Returns:
        Workspace name (e.g., "stash-right", "secure-left", "full-right")
    """
    monitor_name = monitor.get("name", "")
    monitor_desc = monitor.get("description", "")

    # Determine side based on monitor
    if "HDMI-A-1" in monitor_name or "L32p-30" in monitor_desc:
        side = "right"
    elif "DP-1" in monitor_name or "P27u-20" in monitor_desc:
        side = "left"
    else:
        print(f"Unknown monitor: {monitor_name} ({monitor_desc}), defaulting to left", file=sys.stderr)
        side = "left"

    return f"{workspace_type}-{side}"


def toggle_monitor_workspace(workspace_type):
    """Toggle a special workspace for the currently active monitor (simple visibility toggle).

    Args:
        workspace_type: Type of workspace ("stash", "secure", or "full")

    Returns:
        0 on success, 1 on error
    """
    monitor = get_active_monitor()
    if not monitor:
        print("Could not determine active monitor", file=sys.stderr)
        return 1

    workspace = get_monitor_workspace(monitor, workspace_type)
    window_manager.toggle_special_workspace(workspace)
    return 0


def toggle_monitor_stash():
    """Toggle the stash workspace for the currently active monitor only."""
    return toggle_monitor_workspace("stash")


def toggle_monitor_secure():
    """Toggle the secure workspace for the currently active monitor only."""
    return toggle_monitor_workspace("secure")


def is_full_workspace_empty(full_workspace):
    """Check if the full workspace is empty."""
    clients = window_manager.run_hyprctl(["clients", "-j"])
    windows_in_full = [
        w for w in clients
        if w.get("workspace", {}).get("name") == f"special:{full_workspace}"
    ]
    return len(windows_in_full) == 0


def toggle_monitor_full():
    """HYPER+F: General toggle for full workspace.

    Logic:
    - In special:full (video) -> hide special:full (peek)
    - In regular workspace:
        - Full empty + video -> fullscreen + move to full + show
        - Full empty + non-video -> show full
        - Full not empty -> show full
    - In stash/secure -> fullscreen in place (existing behavior)

    Returns:
        0 on success, 1 on error
    """
    from . import window_properties

    active_window = window_manager.run_hyprctl(["activewindow", "-j"])
    if not active_window:
        print("No active window")
        return 1

    monitor = get_active_monitor()
    if not monitor:
        print("Could not determine active monitor", file=sys.stderr)
        return 1

    window_class = active_window.get("class", "")
    current_workspace_name = active_window.get("workspace", {}).get("name")
    is_fullscreen = active_window.get("fullscreen", False)
    full_workspace = get_monitor_workspace(monitor, "full")

    # Check if in special:full
    if current_workspace_name == f"special:{full_workspace}":
        # In special:full with video -> hide (peek)
        if is_video_app(window_class):
            window_manager.toggle_special_workspace(full_workspace)
            print(f"Hidden {full_workspace} (peek)")
            return 0

    # Check if in other special workspace (stash/secure)
    if current_workspace_name and current_workspace_name.startswith("special:") and current_workspace_name != f"special:{full_workspace}":
        # In stash/secure -> fullscreen in place
        window_properties.toggle_fullscreen_without_dimming(relative_floating=False)
        return 0

    # In regular workspace
    full_empty = is_full_workspace_empty(full_workspace)

    if full_empty and is_video_app(window_class):
        # Full empty + video -> fullscreen + move to full + show
        if not is_fullscreen:
            window_properties.toggle_fullscreen_without_dimming(relative_floating=False)
        window_manager.run_hyprctl_command(["dispatch", "movetoworkspacesilent", f"special:{full_workspace}"])
        window_manager.toggle_special_workspace(full_workspace)
        print(f"Moved video to {full_workspace} and fullscreened")
    else:
        # Full empty + non-video OR full not empty -> show full
        window_manager.toggle_special_workspace(full_workspace)
        print(f"Toggled {full_workspace} visibility")

    return 0


def full_video_enter_exit():
    """SUPER CTRL+F: Video enter/exit for full workspace.

    Logic:
    - In special:full (video) -> unfullscreen + move to regular + hide full (exit)
    - In regular OR other special workspace:
        - Full empty + video -> fullscreen + move to full + show
        - Full not empty + video -> error (taken)
        - Non-video -> same as HYPER+F

    Returns:
        0 on success, 1 on error
    """
    from . import window_properties

    active_window = window_manager.run_hyprctl(["activewindow", "-j"])
    if not active_window:
        print("No active window")
        return 1

    monitor = get_active_monitor()
    if not monitor:
        print("Could not determine active monitor", file=sys.stderr)
        return 1

    window_class = active_window.get("class", "")
    current_workspace_name = active_window.get("workspace", {}).get("name")
    is_fullscreen = active_window.get("fullscreen", False)
    full_workspace = get_monitor_workspace(monitor, "full")

    # Check if in special:full with video
    if current_workspace_name == f"special:{full_workspace}" and is_video_app(window_class):
        # Exit: unfullscreen + move to regular + hide full
        target_workspace = monitor.get("activeWorkspace", {}).get("id")

        if is_fullscreen:
            window_properties.toggle_fullscreen_without_dimming(relative_floating=False)

        window_manager.run_hyprctl_command(["dispatch", "movetoworkspacesilent", str(target_workspace)])
        window_manager.toggle_special_workspace(full_workspace)
        print(f"Exited {full_workspace}: moved to workspace {target_workspace}")
        return 0

    # In regular OR other special workspace
    full_empty = is_full_workspace_empty(full_workspace)

    if is_video_app(window_class):
        if full_empty:
            # Full empty + video -> fullscreen + move to full + show
            if not is_fullscreen:
                window_properties.toggle_fullscreen_without_dimming(relative_floating=False)
            window_manager.run_hyprctl_command(["dispatch", "movetoworkspacesilent", f"special:{full_workspace}"])
            window_manager.toggle_special_workspace(full_workspace)
            print(f"Moved video to {full_workspace} and fullscreened")
        else:
            # Full not empty + video -> error
            error_msg = f"Error: {full_workspace} is already occupied"
            print(error_msg, file=sys.stderr)
            subprocess.run([
                "dunstify",
                "-a", "hypr-window-ops",
                "-u", "critical",
                "-t", "3000",
                "Full Workspace Occupied",
                f"Cannot move video to {full_workspace} - already in use"
            ], check=False)
            return 1
    else:
        # Non-video -> same as HYPER+F
        return toggle_monitor_full()

    return 0


def move_to_monitor_workspace(workspace_type, workspace_name=None):
    """Toggle window between a special workspace and regular workspace.

    If the window is in a special workspace, moves it to the regular workspace.
    If the window is in a regular workspace, moves it to the special workspace.

    Args:
        workspace_type: Type of workspace ("stash", "secure", or "full")
        workspace_name: Optional specific workspace name to use (e.g., "stash-left").
                       If not provided, automatically determines based on current monitor.

    Returns:
        0 on success, 1 on error
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

    # Otherwise, move to special workspace
    if workspace_name:
        workspace = workspace_name
    else:
        # Auto-detect based on current monitor
        monitor = get_active_monitor()
        if not monitor:
            print("Could not determine active monitor")
            return 1

        workspace = get_monitor_workspace(monitor, workspace_type)

    # Move the active window to the appropriate workspace
    window_manager.run_hyprctl_command(["dispatch", "movetoworkspacesilent", f"special:{workspace}"])

    print(f"Moved window to {workspace}")
    return 0


def move_to_monitor_stash(stash_name=None):
    """Toggle window between stash and regular workspace."""
    return move_to_monitor_workspace("stash", stash_name)


def move_to_monitor_secure(secure_name=None):
    """Toggle window between secure and regular workspace."""
    return move_to_monitor_workspace("secure", secure_name)


def is_video_app(window_class):
    """Check if a window class is a video app."""
    video_apps = ["mpv", "vlc", "jellyfin-mpv", "mpv-svtplay"]
    return any(app in window_class.lower() for app in video_apps)