#!/bin/bash

# This script is used to change the browser used when links are opened from inside an app
# depending on which app opens the link. hyprctl is used to monitor the active window at the time
# the link is opened.

# Default browser in case the active window doesn't match any entry in the mapping
default_browser="vivaldi-stable.desktop"

while true; do
    # Variable to store the active window name
    active_window_class=$(hyprctl activewindow -j | jq -r '.class')
    # Variable to store the active window title
    active_window_title=$(hyprctl activewindow -j | jq -r '.title')

    # Define a mapping between window classes and the browsers to use
    declare -A window_browser_map
    window_browser_map["chromium"]="chromium.desktop"
    window_browser_map["Slack"]="chromium.desktop"
    # For the VSCodium window class, look at the title and set the browser accordingly
    if [ "$active_window_class" = "Code" ]; then
        if [[ "$active_window_title" =~ " Work " ]]; then
            window_browser_map["Code"]="chromium.desktop"
        else
            window_browser_map["Code"]="vivaldi-stable.desktop"
        fi
    fi

    # Check if the active window name is in the mapping
    if [ -v window_browser_map["$active_window_class"] ]; then
        selected_browser="${window_browser_map[$active_window_class]}"
    else
        selected_browser="$default_browser"
    fi

    # Set xdg-settings to the selected browser
    unset BROWSER
    xdg-settings set default-web-browser "$selected_browser"

    # Optionally, you can print some information for debugging
    # echo "Active Window: $active_window_class"
    # echo "Active Window Title: $active_window_title"
    # echo "Selected Browser: $selected_browser"
sleep 1
done
