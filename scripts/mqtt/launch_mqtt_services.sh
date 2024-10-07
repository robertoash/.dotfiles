#!/bin/bash

# Make logging_utils available
export PYTHONPATH="$PYTHONPATH:/home/rash/.config/scripts"

# Ensure the current directory is where .envrc is located
cd /home/rash/.config/scripts/mqtt || exit

# Source same path as .zshrc
source /home/rash/.config/zsh/.zsh_path

# ASDF
. /opt/asdf-vm/asdf.sh

eval "$(direnv export bash)"

# Initialize debug argument
debug_arg=""

# Check if --debug is provided in either argument
if [[ "$1" == "--debug" ]]; then
    debug_arg="--debug"
    service="$2"
elif [[ "$2" == "--debug" ]]; then
    debug_arg="--debug"
    service="$1"
else
    service="$1"
fi

# Determine which service to start based on the argument
if [[ "$service" == "mqtt_reports" ]]; then
    python3 /home/rash/.config/scripts/mqtt/mqtt_reports.py $debug_arg
elif [[ "$service" == "mqtt_listener" ]]; then
    python3 /home/rash/.config/scripts/mqtt/mqtt_listener.py $debug_arg
else
    echo "Invalid service. Use 'mqtt_reports' or 'mqtt_listener'."
    exit 1
fi
