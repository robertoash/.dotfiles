#!/bin/bash

# Function to handle the selected action
handle_action() {
    case "$1" in
        open)
            xdg-open "$2"
            ;;
        copy_path)
            echo -n "$2" | wl-copy
            ;;
        copy_file)
            wl-copy < "$2"
            ;;
    esac
}

# Locate files and select one using Rofi
FILE=$(locate home media | rofi -theme ~/.config/rofi/current_theme_single_column.rasi -dmenu -p "Locate File")

# If no file is selected, exit
[ -z "$FILE" ] && exit

# Choose an action for the selected file
ACTION=$(echo -e "open\ncopy_path\ncopy_file" | rofi -theme ~/.config/rofi/current_theme_single_column.rasi -dmenu -p "Action for $FILE")

# If no action is selected, exit
[ -z "$ACTION" ] && exit

# Handle the selected action
handle_action "$ACTION" "$FILE"
