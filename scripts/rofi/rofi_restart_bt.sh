#!/usr/bin/env bash

declare -A LABELS
declare -A COMMANDS

## Define commands

# restart bluetooth
COMMANDS["restart_bt"]="systemctl restart bluetooth.service; if [ $? -eq 0 ]; then notify-send 'Bluetooth restarted successfully'; else notify-send 'Bluetooth restart failed'; fi"
LABELS["restart_bt"]=""

################################################################################
# main script (don't touch below)
################################################################################

# Generate menu
function print_menu() {
    for key in "${!LABELS[@]}"; do
        echo "$key"
        # echo "$key  ${LABELS[$key]}"
    done
}

# Show rofi
function start() {
    print_menu | rofi -dmenu -i -theme-str 'entry { placeholder: "Restart Bluetooth..."; }'
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
