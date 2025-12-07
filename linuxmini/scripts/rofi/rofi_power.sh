#!/usr/bin/env bash

declare -A LABELS
declare -A COMMANDS

## Define commands

COMMANDS["lock"]="hyprlock --immediate"
LABELS["lock"]=""

COMMANDS["logout"]="hyprctl dispatch exit"
LABELS["logout"]=""

COMMANDS["reboot"]="systemctl reboot"
LABELS["reboot"]=""

COMMANDS["power_off"]="systemctl poweroff"
LABELS["power_off"]=""

# Define display order
ORDER=("lock" "logout" "reboot" "power_off")

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
    print_menu | rofi -dmenu -i -theme-str 'entry { placeholder: "Shutdown actions..."; }'
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
