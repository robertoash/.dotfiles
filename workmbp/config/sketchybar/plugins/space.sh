#!/usr/bin/env bash
export PATH="/etc/profiles/per-user/rash/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
if [ "$SELECTED" = "true" ]; then
    sketchybar --set $NAME background.drawing=on \
                            background.color=0xff7aa2f7 \
                            icon.color=0xff1e1e2e
else
    sketchybar --set $NAME background.drawing=off \
                            icon.color=0xffffffff
fi
