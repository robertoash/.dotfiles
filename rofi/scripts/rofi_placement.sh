#!/bin/bash

# This script is used to determine the correct location of the
# Rofi launcher, depending on whether the active monitor is
# rotated vertically or not.


# Variable to store the monitor ID with the active workspace
monitor_index=$(hyprctl activeworkspace -j | jq '.monitorID')

# Variable to store whether the active monitor is vertical or horizontal
is_vertical=$(hyprctl monitors -j | jq --argjson monitor_index ${monitor_index} '.[$monitor_index].transform')

# For the VSCodium window class, look at the title and set the>
if [ "$is_vertical" = "1" ]; then
    monitor_orientation="vertical"
    monitor_width=$(hyprctl monitors -j | jq --argjson monitor_index ${monitor_index} '.[$monitor_index].height')
    monitor_height=$(hyprctl monitors -j | jq --argjson monitor_index ${monitor_index} '.[$monitor_index].width')
else
    monitor_orientation="horizontal"
    monitor_width=$(hyprctl monitors -j | jq --argjson monitor_index ${monitor_index} '.[$monitor_index].width')
    monitor_height=$(hyprctl monitors -j | jq --argjson monitor_index ${monitor_index} '.[$monitor_index].height')
fi

#
rofi_width=384
rofi_height=191

new_x=$(awk -v monitor_width="$monitor_width" -v rofi_width="$rofi_width" 'BEGIN {print (monitor_width / 2) - rofi_width}')
new_y=$(awk -v monitor_height="$monitor_height" -v rofi_height="$rofi_height" 'BEGIN {print (monitor_height / 2) - rofi_height}')

# Optionally, you can print some information for debugging
#echo "Active Monitor is: $monitor_orientation"
#echo "Monitor Width is: $monitor_width"
#echo "Monitor Height is: $monitor_height"
#echo "Rofi positioned at: X=$new_x, Y=$new_y"

echo "-location 1 -xoffset $new_x -yoffset $new_y"



