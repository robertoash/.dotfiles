#!/bin/bash

# Kill all dunst instances
killall dunst
# Start dunst with the custom config file
dunst -conf /home/rash/.config/dunst/dunst.config &
# Notify of the reload
dunstify "Dunst has been reloaded." --icon=dialog-information --timeout=5000
