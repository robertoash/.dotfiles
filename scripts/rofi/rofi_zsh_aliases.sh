#!/usr/bin/env bash

SELECTED_ALIAS=$(awk '/^alias/ {
    gsub(/alias|[\042\047]/, "")
    split($0, parts, /#/)
    split(parts[1], cmd, /=/)
    name = cmd[1]
    command = cmd[2]
    description = (parts[2] ? parts[2] : "")
    gsub(/^ +| +$/, "", name)
    gsub(/^ +| +$/, "", command)
    gsub(/^ +| +$/, "", description)
    output = sprintf("%s - %s [%s]", name, description, command)
    gsub(/ +/, " ", output)
    print output
}' ~/.config/zsh/.zsh_aliases | \
rofi -theme ~/.config/rofi/current_theme_single_column.rasi \
-dmenu -i -threads 0 -width 100 -p "zsh_aliases:")

# If no file is selected, exit
[ -z "$SELECTED_ALIAS" ] && exit

# Extract the alias name from the selected line
alias=$(echo "$SELECTED_ALIAS" | awk -F' - ' '{print $1}')

# Copy the alias to the clipboard
echo -n "$alias" | wl-copy
