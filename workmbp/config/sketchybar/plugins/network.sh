#!/usr/bin/env bash
export PATH="/etc/profiles/per-user/rash/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

WIFI_STATUS=$(networksetup -getairportnetwork en0 | awk -F': ' '{print $2}')
if [ "$WIFI_STATUS" = "You are not associated with an AirPort network." ]; then
    sketchybar --set network icon="󰌙"
else
    # Just use connected icon since airport command is deprecated in macOS Tahoe
    sketchybar --set network icon="󰤨"
fi
