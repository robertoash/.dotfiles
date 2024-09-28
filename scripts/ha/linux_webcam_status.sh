#!/bin/bash

DEVICE_FILE="/dev/video0"
LAST_STATE="inactive"  # Track the last state to avoid duplicate calls

# Load the environment variables using the custom script
eval $(/home/rash/.config/scripts/shell/secure_env_secrets.py)

# Function to check if the webcam is in use by a process
is_webcam_in_use() {
    lsof "$DEVICE_FILE" 2>/dev/null | grep "$DEVICE_FILE" > /dev/null
    return $?
}

# Function to notify Home Assistant
notify_home_assistant() {
    local state=$1
    local service_call="input_boolean.turn_off"

    if [[ "$state" == "active" ]]; then
        service_call="input_boolean.turn_on"
    fi

    # Call hass-cli using the environment variables loaded from the secure_env_secrets.py script
    # Suppress output and only print if the command fails or succeeds
    if ! /home/rash/.local/bin/hass-cli service call $service_call --arguments entity_id=input_boolean.linux_webcam_active > /dev/null 2>&1; then
        echo "Error: Failed to call Home Assistant service ($service_call)"
    else
        echo "Success: HA boolean updated - Webcam is $state"
    fi
}


# Main loop to monitor webcam activity
while true; do
    # Wait for webcam to become active (inotifywait catches 'open' events)
    inotifywait -m "$DEVICE_FILE" -e open | while read -r path action file; do

        # When inotifywait detects an open event, check if the webcam is actually in use
        if is_webcam_in_use && [[ "$LAST_STATE" == "inactive" ]]; then
            echo "Webcam is active"
            notify_home_assistant "active"
            LAST_STATE="active"
        fi

        # Start polling every 2 seconds to detect when the webcam becomes inactive
        while is_webcam_in_use; do
            sleep 2
        done

        # Once polling detects the webcam is inactive
        if [[ "$LAST_STATE" == "active" ]]; then
            echo "Webcam is inactive"
            notify_home_assistant "inactive"
            LAST_STATE="inactive"
        fi
    done
done
