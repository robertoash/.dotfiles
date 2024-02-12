#!/usr/bin/env bash

hyprkeys -br -c ~/.config/hypr/keybinds.conf | \
rofi -theme catppuccin_mocha_single_column \
-dmenu -i -threads 0 -width 100 -p "hyprkeys:"
