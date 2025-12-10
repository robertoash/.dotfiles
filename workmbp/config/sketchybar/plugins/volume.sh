#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
VOLUME=$(osascript -e 'output volume of (get volume settings)')
MUTED=$(osascript -e 'output muted of (get volume settings)')

if [ "$MUTED" = "true" ]; then
    /opt/homebrew/bin/sketchybar --set volume icon=󰖁 label=""
else
    if [ "$VOLUME" -ge 70 ]; then
        ICON=󰕾
    elif [ "$VOLUME" -ge 30 ]; then
        ICON=
    else
        ICON=
    fi
    /opt/homebrew/bin/sketchybar --set volume icon="$ICON" label="${VOLUME}%"
fi
