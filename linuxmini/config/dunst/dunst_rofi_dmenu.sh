#!/usr/bin/env bash

# Simple dmenu wrapper that cleans up dunst action display
# without interfering with action return values

# Read input from dunst
input=$(cat)

# Clean each line for display: remove # and everything in parentheses and brackets
# Transform lines like "#🔗 Open Meeting (📅 Calendar Reminder) [7402,open_meeting]"
# into just "🔗 Open Meeting"
cleaned_input=$(echo "$input" | sed -E 's/^#([^(]*)\s*\([^)]*\)\s*\[[^]]*\]$/\1/' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

# If the regex didn't match, try a simpler cleanup
if [[ "$cleaned_input" == "$input" ]]; then
    cleaned_input=$(echo "$input" | sed -E 's/^#//g; s/\s*\([^)]*\)\s*\[[^]]*\]$//g')
fi

# Show cleaned input in rofi
selection=$(echo "$cleaned_input" | /usr/bin/rofi -theme /home/rash/.config/rofi/current_theme_single_column.rasi -dmenu -i -threads 0 -width 100 -theme-str 'entry { placeholder: "choose action...";}')

# If user made a selection, find the corresponding original line and return it
if [[ -n "$selection" ]]; then
    # Find the original line that matches the cleaned selection
    while IFS= read -r original_line; do
        if [[ -n "$original_line" ]]; then
            # Clean this line the same way
            clean_line=$(echo "$original_line" | sed -E 's/^#([^(]*)\s*\([^)]*\)\s*\[[^]]*\]$/\1/' | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')
            if [[ "$clean_line" == "$original_line" ]]; then
                clean_line=$(echo "$original_line" | sed -E 's/^#//g; s/\s*\([^)]*\)\s*\[[^]]*\]$//g')
            fi

            # If this cleaned line matches the user's selection, return the original
            if [[ "$clean_line" == "$selection" ]]; then
                echo "$original_line"
                exit 0
            fi
        fi
    done <<< "$input"
fi