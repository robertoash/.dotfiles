#!/bin/bash

# This script is launched by hypridle when inactivity timeout is reached.
# The config file is here:
# /home/rash/.config/hypr/hypridle.conf

# Step 1: Check lock condition repeatedly until achieved
while true; do
    if [[ $(cat /tmp/mqtt/in_office_status) == "off" ]]; then
        if ! pgrep -x "hyprlock" > /dev/null; then
            hyprlock -q &
        fi
        break
    fi
    sleep 1
done

# Step 2: Wait 30 seconds before managing DPMS state
sleep 30

# Check DPMS condition repeatedly until achieved
while true; do
    if [[ $(cat /tmp/mqtt/in_office_status) == "off" ]]; then
        hyprctl dispatch dpms off
        break
    fi
    sleep 1
done

# Manage DPMS based on in_office_status while locked
# but without issuing duplicate commands
past_status=""
while true; do
    current_status=$(cat /tmp/mqtt/in_office_status)
    if [[ "$current_status" != "$past_status" ]]; then
        if [[ "$current_status" == "on" ]]; then
            hyprctl dispatch dpms on
        else
            hyprctl dispatch dpms off
        fi
        past_status="$current_status"
    fi

    sleep 1
done
