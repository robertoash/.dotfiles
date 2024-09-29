#!/usr/bin/env python3

import subprocess
import time

# This script is launched by hypridle when inactivity timeout is reached.
# The config file is here:
# /home/rash/.config/hypr/hypridle.conf

# Step 1: Check lock condition repeatedly until achieved
while True:
    with open("/tmp/mqtt/in_office_status", "r") as f:
        if f.read().strip() == "off":
            if (
                not subprocess.run(
                    ["pgrep", "-x", "hyprlock"], capture_output=True
                ).returncode
                == 0
            ):
                subprocess.Popen(["hyprlock", "-q"])
            break
    time.sleep(1)

# Step 2: Wait 10 seconds before managing DPMS state
time.sleep(10)

# Check DPMS condition repeatedly until achieved
while True:
    with open("/tmp/mqtt/in_office_status", "r") as f:
        if f.read().strip() == "off":
            subprocess.run(["hyprctl", "dispatch", "dpms", "off"])
            break
    time.sleep(1)

# Manage DPMS based on in_office_status while locked
# but without issuing duplicate commands and only during work hours
past_status = ""
while True:
    if time.localtime().tm_hour >= 6 and time.localtime().tm_hour <= 20:
        with open("/tmp/mqtt/in_office_status", "r") as f:
            current_status = f.read().strip()
        if current_status != past_status:
            if current_status == "on":
                subprocess.run(["hyprctl", "dispatch", "dpms", "on"])
            else:
                subprocess.run(["hyprctl", "dispatch", "dpms", "off"])
            past_status = current_status
    time.sleep(1)
