#!/usr/bin/env bash
export PATH="/etc/profiles/per-user/rash/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
FRONT_APP=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true')
sketchybar --set front_app label="$FRONT_APP"
