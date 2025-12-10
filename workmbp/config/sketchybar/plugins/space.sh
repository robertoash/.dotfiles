#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
if [ "$SELECTED" = "true" ]; then
    /opt/homebrew/bin/sketchybar --set $NAME background.drawing=on \
                            background.color=0xff7aa2f7 \
                            icon.color=0xff1e1e2e
else
    /opt/homebrew/bin/sketchybar --set $NAME background.drawing=off \
                            icon.color=0xffffffff
fi
