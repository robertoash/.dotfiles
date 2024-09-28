#!/bin/bash

# Step 1: Check lock condition repeatedly
while true; do
    if [[ $(cat /tmp/in_office_pure_status) == "off" ]]; then
        echo "$(date): Locking screen" >> "$LOGFILE"
        hyprlock -q &
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
