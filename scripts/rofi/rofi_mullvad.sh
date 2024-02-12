#!/usr/bin/env bash

declare -A LABELS
declare -A COMMANDS

## Define commands

# get mullvad status and show notification
COMMANDS["status"]="notify-send '$(mullvad status)'"
LABELS["status"]=""

# connect to mullvad and show notification
COMMANDS["connect"]="mullvad connect; sleep 2; notify-send 'Mullvad Status' \"\$(mullvad status)\""
LABELS["connect"]=""

# disconnect from mullvad and show notification
COMMANDS["disconnect"]="mullvad disconnect; sleep 2; notify-send 'Mullvad Status' \"\$(mullvad status)\""
LABELS["disconnect"]=""

# Define display order
ORDER=("status" "connect" "disconnect")

################################################################################
# main script (don't touch below)
################################################################################

# Generate menu
function print_menu() {
    for key in "${ORDER[@]}"; do
        echo "$key"
        # echo "$key  ${LABELS[$key]}"
    done
}

# Show rofi
function start() {
    print_menu | rofi -dmenu -p "Mullvad: " -i
}

# Run it
choice="$(start)"

# Cancelled? bail out
if [[ -z $choice ]]; then
    exit
fi

# Extract command
command=${COMMANDS[$choice]}

# Check if command exists
if [[ -n $command ]]; then
    eval "$command"
else
    echo "Unknown command: $choice" | rofi -dmenu -p "Error"
fi
