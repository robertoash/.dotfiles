#!/usr/bin/env python3

import json
import subprocess


# Function to execute a shell command and return the output
def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


# Get the active window's address and fullscreen status
active_window_json = run_command("hyprctl activewindow -j")
active_window = json.loads(active_window_json)
window_id = active_window.get("address")
fullscreen = active_window.get("fullscreen")

if fullscreen:
    # Exit fullscreen and remove nodim property
    run_command("hyprctl dispatch fullscreen")
    run_command(f"hyprctl setprop address:{window_id} nodim 0")
else:
    # Enter fullscreen and set nodim property
    run_command("hyprctl dispatch fullscreen")
    run_command(f"hyprctl setprop address:{window_id} nodim 1")
