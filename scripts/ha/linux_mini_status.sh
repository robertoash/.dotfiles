#!/bin/bash

LAST_STATE="inactive"  # Track the last state to avoid duplicate calls

# Load the environment variables using the custom script
eval $(/home/rash/.config/scripts/shell/secure_env_secrets.py)

# Function to notify Home Assistant
notify_home_assistant() {
    local state=$1
    local service_call="input_boolean.turn_off"

    if [[ "$state" == "active" ]]; then
        service_call="input_boolean.turn_on"
    fi

    # Call hass-cli using the environment variables loaded from the secure_env_secrets.py script
    # Suppress output and only print if the command fails or succeeds
    if ! /home/rash/.local/bin/hass-cli service call $service_call --arguments entity_id=input_boolean.linux_mini_active > /dev/null 2>&1; then
        echo "Error: Failed to call Home Assistant service ($service_call)"
    else
        echo "Success: HA boolean updated - Linux Mini is $state"
    fi
}

# Parse command line arguments
case "$1" in
    --active)
        state="active"
        ;;
    --inactive)
        state="inactive"
        ;;
    *)
        exit 1
        ;;
esac

# Notify Home Assistant
notify_home_assistant "$state"

