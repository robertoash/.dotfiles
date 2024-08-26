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
monitor = active_window.get("monitor")

if monitor == 1:
    new_width = "704"
    new_height = "396"
else:
    new_width = "853"
    new_height = "480"

if floating:
    # Float the window and resize
    run_command("hyprctl dispatch togglefloating")
else:
    # Float the window and resize
    run_command("hyprctl dispatch togglefloating")
    run_command(f"hyprctl dispatch resizeactive exact {new_width} {new_height}")
    run_command("~/.config/scripts/hyprland/snap_window_to_corner.py --lower-right")
