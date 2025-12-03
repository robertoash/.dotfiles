#!/usr/bin/env bash
export PATH="/etc/profiles/per-user/rash/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
TIME_LOCAL=$(date "+%H:%M:%S")
sketchybar --set clock label="$TIME_LOCAL"
