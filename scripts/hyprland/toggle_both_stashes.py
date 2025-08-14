#!/usr/bin/env python3

import json
import subprocess
import sys


def run_hyprctl(args):
    """Run hyprctl command and return parsed JSON output."""
    result = subprocess.run(["hyprctl"] + args, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running hyprctl {' '.join(args)}: {result.stderr}", file=sys.stderr)
        return None
    return json.loads(result.stdout) if result.stdout.strip() else None


def dispatch(command, arg=None):
    """Send a dispatch command to hyprctl."""
    cmd = ["dispatch", command]
    if arg:
        cmd.append(arg)
    subprocess.run(["hyprctl"] + cmd, check=True)


def get_current_monitor():
    """Get the currently focused monitor name."""
    monitors = run_hyprctl(["-j", "monitors"])
    if not monitors:
        return None
    
    for monitor in monitors:
        if monitor.get("focused", False):
            return monitor["name"]
    return None


def toggle_active_monitor():
    """Toggle focus to the opposite monitor using the existing script."""
    subprocess.run(["/home/rash/.config/scripts/hyprland/toggle_active_monitor.py"], check=True)


def count_open_stashes():
    """Count how many stash workspaces are currently visible and return their details."""
    monitors = run_hyprctl(["-j", "monitors"])
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
    """Get the monitor name that should have the specified stash."""
    if stash_name == "stash-left":
        return "DP-3"  # P27u-20 monitor
    elif stash_name == "stash-right":
        return "DP-1"  # L32p-30 monitor
    return None


def main():
    # Store original monitor to return focus later
    original_monitor = get_current_monitor()
    if not original_monitor:
        print("Could not determine current monitor", file=sys.stderr)
        return 1
    
    # Check current state of stash workspaces
    open_count, open_stashes = count_open_stashes()
    
    if open_count == 0:
        # No stashes open - open both
        print("No stashes open, opening both...")
        
        # Move to opposite monitor and launch its stash
        toggle_active_monitor()
        dispatch("togglespecialworkspace", "stash-left")
        
        # Move back and launch this monitor's stash  
        toggle_active_monitor()
        dispatch("togglespecialworkspace", "stash-right")
        
    elif open_count == 2:
        # Both stashes open - close both using same process
        print("Both stashes open, closing both...")
        
        # Move to opposite monitor and toggle off its stash
        toggle_active_monitor()
        dispatch("togglespecialworkspace", "stash-left")
        
        # Move back and toggle off this monitor's stash
        toggle_active_monitor() 
        dispatch("togglespecialworkspace", "stash-right")
        
    elif open_count == 1:
        # Only one stash open - toggle only that one
        stash_info = open_stashes[0]
        stash_name = stash_info["stash"].replace("special:", "")
        target_monitor = get_monitor_for_stash(stash_name)
        
        print(f"One stash open ({stash_name}), toggling it off...")
        
        # Focus the correct monitor and toggle only that stash
        dispatch("focusmonitor", target_monitor)
        dispatch("togglespecialworkspace", stash_name)
    
    # Return focus to original monitor
    dispatch("focusmonitor", original_monitor)
    return 0


if __name__ == "__main__":
    sys.exit(main())