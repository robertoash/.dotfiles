#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
FRONT_APP=$(osascript -e 'tell application "System Events" to get name of first application process whose frontmost is true')
/opt/homebrew/bin/sketchybar --set front_app label="$FRONT_APP"
