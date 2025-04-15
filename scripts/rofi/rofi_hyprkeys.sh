#!/usr/bin/env bash

hyprkeys -br -c ~/.config/hypr/keybinds.conf | \
rofi -theme ~/.config/rofi/current_theme_single_column.rasi \
-dmenu -i -threads 0 -width 100 -theme-str 'entry { placeholder: "hyprkeys filter..."; }'
