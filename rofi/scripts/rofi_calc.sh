#!/usr/bin/env bash

# Run script to place rofi correctly on active screen
rofi_placement="$(/home/rash/.config/rofi/scripts/rofi_placement.sh)"

# Run calc
rofi -show calc -modi calc -no-show-match -no-sort $rofi_placement
