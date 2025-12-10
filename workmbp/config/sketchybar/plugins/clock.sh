#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
TIME_LOCAL=$(date "+%H:%M:%S")
/opt/homebrew/bin/sketchybar --set clock label="$TIME_LOCAL"
