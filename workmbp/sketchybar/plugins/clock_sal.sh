#!/usr/bin/env bash
export PATH="/etc/profiles/per-user/rash/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
TIME_SAL=$(TZ="America/El_Salvador" date "+%H:%M")
sketchybar --set clock.sal label="$TIME_SAL"
