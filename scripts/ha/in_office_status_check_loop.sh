#!/bin/bash

# This script is launched by hypridle when inactivity timeout is reached.
# The config file is here:
# /home/rash/.config/hypr/hypridle.conf

# Step 1: Check lock condition repeatedly
while true; do
    if [[ $(cat /tmp/in_office_pure_status) == "off" ]]; then
        if ! pgrep -x "hyprlock" > /dev/null; then
            hyprlock -q &
        fi
        break
    fi
    sleep 1
done

# Step 2: Wait 30 seconds before managing DPMS state
sleep 30

# Check DPMS condition repeatedly
while true; do
    if [[ $(cat /tmp/in_office_pure_status) == "off" ]]; then
        hyprctl dispatch dpms off
        break
    fi
    sleep 1
done
