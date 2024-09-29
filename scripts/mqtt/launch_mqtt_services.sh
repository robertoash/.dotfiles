#!/bin/bash

# Make logging_utils available
export PYTHONPATH="$PYTHONPATH:/home/rash/.config/scripts"

# Ensure the current directory is where .envrc is located
cd /home/rash/.config/scripts/mqtt || exit

# Source same path as .zshrc
source /home/rash/.config/zsh/.zsh_path

eval "$(direnv export bash)"

python /home/rash/.config/scripts/mqtt/mqtt_reports.py &
python /home/rash/.config/scripts/mqtt/mqtt_listener.py &


