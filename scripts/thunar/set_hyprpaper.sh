#! /bin/bash

# Script to put an image in the right location using Thunar
# for Hyperpaper to use it as a wallpaper

# Get the image path
image_path="$1"

# Get the desired position (left or right)
position="$2"

# Delete existing wallpaper file (with the format hypr_position.*)
/usr/bin/rm -f /home/rash/.config/wallpaper/hypr_"$position".*

# Copy the image to the wallpaper folder keeping the same extension
/usr/bin/cp "$image_path" /home/rash/.config/wallpaper/hypr_"$position"."${image_path##*.}"

# Modify ~/.config/hypr/hyprpaper.conf to use the new wallpaper
# Read the file and replace instances of hypr_position.* with the new wallpaper
/usr/bin/sed -i "s/hypr_$position\.[a-zA-Z0-9]*/hypr_$position.${image_path##*.}/" /home/rash/.config/hypr/hyprpaper.conf

# Kill the hyprpaper process and reload
/usr/bin/killall hyprpaper
/usr/bin/hyprpaper &
