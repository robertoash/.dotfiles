#!/usr/bin/env bash

# Connect to offlinelab and get directory sizes
ssh offlinelab "du --all --max-depth=1 -h /media/offline_data/data/media/films/ | \
sort -rh | awk 'NR==1 {sub(/\\/media\\/offline_data\\/data\\/media\\/films\\//, \
\"TOTAL\"); print; next} {gsub(/\\/media\\/offline_data\\/data\\/media\\/films\\//, \
\"\"); print}'" | \
# Display results in a rofi menu
rofi -theme catppuccin_mocha_single_column -dmenu -i -threads 0 -width 100 \
-p "media_size:"
