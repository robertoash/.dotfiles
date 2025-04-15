#!/usr/bin/env bash

# Connect to offlinelab and get directory sizes
ssh offlinelab "du --all --max-depth=2 -h /media/offline_data/data/media/ | sort -rh | awk 'NR==1 {sub(/\\/media\\/offline_data\\/data\\/media\\//, \"\"); printf \"%-6s %-s\\n\", \"TOTAL\", \$1; next} {gsub(/\\/media\\/offline_data\\/data\\/media\\//, \"\"); gsub(/[ ()]/, \"_\"); \$2 = tolower(\$2); gsub(/__+/, \"_\", \$2); gsub(/_$/, \"\", \$2); printf \"%-6s %-s\\n\", \$1, \$2}'" | \
# Display results in a rofi menu
rofi -theme ~/.config/rofi/current_theme_single_column.rasi -dmenu -i -threads 0 -width 100 -lines 50 \
-theme-str 'entry { placeholder: "media_size..."; }'
