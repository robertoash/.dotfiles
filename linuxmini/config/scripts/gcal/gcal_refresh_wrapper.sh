#!/bin/bash
#
# Cache refresh wrapper for gcal_notify.py
# Refreshes the event cache from Google Calendar API
# Should be run every 30 minutes to keep cache fresh
#

# Set up environment variables
export DISPLAY=:0
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export PULSE_RUNTIME_PATH="/run/user/$(id -u)/pulse"
export WAYLAND_DISPLAY="wayland-1"

# Add common paths - make sure .local/bin is included
export PATH="/home/rash/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# Set HOME if not set
export HOME="/home/rash"

# Change to the script directory
cd "/home/rash/.config/scripts/gcal"

# Log the refresh operation
{
    echo "=== Cache refresh started at $(date) ==="
    echo "DISPLAY: $DISPLAY"
    echo "XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
    echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
    echo "PATH: $PATH"
    echo "PWD: $(pwd)"
    echo "Running gcal_notify.py --refresh --verbose"
    echo "=================================="
} >> "/home/rash/.config/gcal-notifications/refresh.log" 2>&1

# Run the refresh to update cache from API
python3 "/home/rash/.config/scripts/gcal/gcal_notify.py" --refresh >> "/home/rash/.config/gcal-notifications/refresh.log" 2>&1

# Log completion
echo "=== Cache refresh completed at $(date) ===" >> "/home/rash/.config/gcal-notifications/refresh.log" 2>&1