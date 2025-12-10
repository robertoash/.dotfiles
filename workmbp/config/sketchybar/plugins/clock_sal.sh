#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
TIME_SAL=$(TZ="America/El_Salvador" date "+%H:%M")
/opt/homebrew/bin/sketchybar --set clock.sal label="$TIME_SAL"
