#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Collect battery information using pmset (single call)
BATTERY_DATA=$(pmset -g batt)
BATTERY_INFO=$(echo "$BATTERY_DATA" | grep -Eo "[0-9]+%" | head -1)
PERCENTAGE=${BATTERY_INFO%\%}

# Fallback to 0 if parsing failed
if [ -z "$PERCENTAGE" ]; then
    PERCENTAGE=0
fi

# Determine if device is charging
if echo "$BATTERY_DATA" | grep -q "AC Power"; then
    CHARGING=true
else
    CHARGING=false
fi

# Choose icon based on charge level and charging state
if [ "$CHARGING" = true ]; then
    ICON=󰂄
else
    if [ "$PERCENTAGE" -ge 80 ]; then
        ICON=󰁹
    elif [ "$PERCENTAGE" -ge 60 ]; then
        ICON=󰂀
    elif [ "$PERCENTAGE" -ge 40 ]; then
        ICON=󰁿
    elif [ "$PERCENTAGE" -ge 20 ]; then
        ICON=󰁽
    else
        ICON=󰂃
    fi
fi

# Update SketchyBar item with icon and label
/opt/homebrew/bin/sketchybar --set "$NAME" icon="$ICON" label="${PERCENTAGE}%"
