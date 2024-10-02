#!/bin/bash

# Make logging_utils available
export PYTHONPATH="$PYTHONPATH:/home/rash/.config/scripts"

# Ensure the current directory is where .envrc is located
cd /home/rash/.config/scripts/mqtt || exit

# Source same path as .zshrc
source /home/rash/.config/zsh/.zsh_path

eval "$(direnv export bash)"

# Check if --debug argument is provided
if [[ "$1" == "--debug" ]]; then
    debug_arg="--debug"
else
    debug_arg=""
fi

python3 /home/rash/.config/scripts/mqtt/mqtt_reports.py $debug_arg &
python3 /home/rash/.config/scripts/mqtt/mqtt_listener.py $debug_arg &


