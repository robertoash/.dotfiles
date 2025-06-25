#!/bin/bash
#
# Cron wrapper for gcal_notify.py
# Sets up the environment needed for GUI applications to work from cron
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

# Log the environment for debugging (optional - can be removed later)
{
    echo "=== Cron job started at $(date) ==="
    echo "DISPLAY: $DISPLAY"
    echo "XDG_RUNTIME_DIR: $XDG_RUNTIME_DIR"
    echo "WAYLAND_DISPLAY: $WAYLAND_DISPLAY"
    echo "PATH: $PATH"
    echo "PWD: $(pwd)"
    echo "Running gcal_notify.py --cron --verbose"
    echo "=================================="
} >> "/home/rash/.config/gcal-notifications/cron.log" 2>&1

# Run the actual script with full path and verbose output
python3 "/home/rash/.config/scripts/gcal/gcal_notify.py" --cron --verbose >> "/home/rash/.config/gcal-notifications/cron.log" 2>&1

# Log completion
echo "=== Cron job completed at $(date) ===" >> "/home/rash/.config/gcal-notifications/cron.log" 2>&1