#!/bin/bash

# Set PYTHONPATH to ensure logging_utils is available
export PYTHONPATH="$PYTHONPATH:/home/rash/.config/scripts"

# Ensure we are in the correct working directory
cd /home/rash/.config/scripts/mqtt || exit 1

# Manually source .env to load secrets (since systemd won't trigger mise)
source /home/rash/.config/scripts/mqtt/.env

# Initialize debug argument
debug_arg=""

# Check if --debug is provided
if [[ "$1" == "--debug" ]]; then
    debug_arg="--debug"
    service="$2"
elif [[ "$2" == "--debug" ]]; then
    debug_arg="--debug"
    service="$1"
else
    service="$1"
fi

# Determine which service to start (using system Python)
if [[ "$service" == "mqtt_reports" ]]; then
    /usr/bin/python3 /home/rash/.config/scripts/mqtt/mqtt_reports.py $debug_arg
elif [[ "$service" == "mqtt_listener" ]]; then
    /usr/bin/python3 /home/rash/.config/scripts/mqtt/mqtt_listener.py $debug_arg
else
    echo "Invalid service. Use 'mqtt_reports' or 'mqtt_listener'."
    exit 1
fi
