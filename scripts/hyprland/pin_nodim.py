#!/usr/bin/env python3

import json
import subprocess


# Function to execute a shell command and return the output
def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


# Get the active window's address and pin status
active_window_json = run_command("hyprctl activewindow -j")
active_window = json.loads(active_window_json)
window_id = active_window.get("address")
floating = active_window.get("floating")
pinned = active_window.get("pinned")

if pinned:
    # Unpin the window and remove nodim property
    run_command("hyprctl dispatch pin")
    run_command(f"hyprctl setprop address:{window_id} nodim 0")
else:
    # Float the window first if it's not already floating
    if not floating:
        run_command("~/.config/scripts/hyprland/lagom_floating.py")
    # Pin the window and set nodim property
    run_command("hyprctl dispatch pin")
    run_command(f"hyprctl setprop address:{window_id} nodim 1")
    run_command("~/.config/scripts/hyprland/snap_window_to_corner.py --lower-right")
