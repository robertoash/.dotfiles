#!/usr/bin/env bash

declare -A LABELS
declare -A COMMANDS

## Define commands

COMMANDS["start_ipad"]="systemctl --user start sunshine-ipad"
LABELS["start_ipad"]="▶"

COMMANDS["stop_ipad"]="systemctl --user stop sunshine-ipad"
LABELS["stop_ipad"]="■"

COMMANDS["status"]="systemctl --user status sunshine-ipad"
LABELS["status"]="ℹ"

# Define display order
ORDER=("start_ipad" "stop_ipad" "status")

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
    print_menu | rofi -dmenu -i -theme-str 'entry { placeholder: "Sunshine iPad..."; }'
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
