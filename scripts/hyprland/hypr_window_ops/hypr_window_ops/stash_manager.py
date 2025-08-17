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


def toggle_active_monitor():
    """Toggle focus to the opposite monitor using the existing script."""
    subprocess.run(["/home/rash/.config/scripts/hyprland/toggle_active_monitor.py"], check=True)


def count_open_stashes():
    """Count how many stash workspaces are currently visible and return their details."""
    monitors = window_manager.run_hyprctl(["monitors", "-j"])
    if not monitors:
        return 0, []
    
    open_stashes = []
    for monitor in monitors:
        special_ws = monitor.get("specialWorkspace", {})
        if special_ws.get("name") in ["special:stash-left", "special:stash-right"]:
            open_stashes.append({
                "monitor": monitor["name"],
                "stash": special_ws["name"],
                "monitor_desc": monitor.get("description", "")
            })
    
    return len(open_stashes), open_stashes


def get_monitor_for_stash(stash_name):
    """Get the monitor name that should have the specified stash based on description."""
    monitors = window_manager.run_hyprctl(["monitors", "-j"])
    if not monitors:
        return None
    
    target_desc = None
    if stash_name == "stash-left":
        target_desc = "Lenovo Group Limited P27u-20 V90CHVAB"
    elif stash_name == "stash-right":
        target_desc = "Lenovo Group Limited L32p-30 U51250AL"
    
    if not target_desc:
        return None
    
    for monitor in monitors:
        if monitor.get("description") == target_desc:
            return monitor.get("name")
    
    return None


def toggle_both_stashes():
    """Toggle both stash workspaces intelligently based on current state."""
    # Store original monitor to return focus later
    original_monitor_info = get_active_monitor()
    if not original_monitor_info:
        print("Could not determine current monitor", file=sys.stderr)
        return 1
    
    original_monitor = original_monitor_info["name"]
    
    # Check current state of stash workspaces
    open_count, open_stashes = count_open_stashes()
    
    if open_count == 0:
        # No stashes open - open both
        print("No stashes open, opening both...")
        
        # Focus correct monitor for stash-left and open it
        left_monitor = get_monitor_for_stash("stash-left")
        if left_monitor:
            window_manager.run_hyprctl_command(["dispatch", "focusmonitor", left_monitor])
            window_manager.toggle_special_workspace("stash-left")
        
        # Focus correct monitor for stash-right and open it
        right_monitor = get_monitor_for_stash("stash-right")
        if right_monitor:
            window_manager.run_hyprctl_command(["dispatch", "focusmonitor", right_monitor])
            window_manager.toggle_special_workspace("stash-right")
        
    elif open_count == 2:
        # Both stashes open - close both using same process
        print("Both stashes open, closing both...")
        
        # Focus correct monitor for stash-left and close it
        left_monitor = get_monitor_for_stash("stash-left")
        if left_monitor:
            window_manager.run_hyprctl_command(["dispatch", "focusmonitor", left_monitor])
            window_manager.toggle_special_workspace("stash-left")
        
        # Focus correct monitor for stash-right and close it
        right_monitor = get_monitor_for_stash("stash-right")
        if right_monitor:
            window_manager.run_hyprctl_command(["dispatch", "focusmonitor", right_monitor])
            window_manager.toggle_special_workspace("stash-right")
        
    elif open_count == 1:
        # Only one stash open - toggle only that one
        stash_info = open_stashes[0]
        stash_name = stash_info["stash"].replace("special:", "")
        target_monitor = get_monitor_for_stash(stash_name)
        
        print(f"One stash open ({stash_name}), toggling it off...")
        
        # Focus the correct monitor and toggle only that stash
        window_manager.run_hyprctl_command(["dispatch", "focusmonitor", target_monitor])
        window_manager.toggle_special_workspace(stash_name)
    
    # Return focus to original monitor
    window_manager.run_hyprctl_command(["dispatch", "focusmonitor", original_monitor])
    return 0


def move_to_monitor_stash(stash_name=None):
    """Move the active window to the appropriate monitor's stash workspace.
    
    Args:
        stash_name: Optional specific stash name to use (e.g., "stash-left", "stash-right").
                   If not provided, automatically determines based on current monitor.
    """
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
        if "DP-2" in monitor_name or "L32p-30" in monitor_desc:
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