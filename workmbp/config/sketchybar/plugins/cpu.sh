#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
CPU_USAGE=$(ps -A -o %cpu | awk -v cores=$(sysctl -n hw.ncpu) '{s+=$1} END {print int(s/cores)}')
# Pad single digit numbers with a leading space for consistent alignment
if [ "$CPU_USAGE" -lt 10 ]; then
    /opt/homebrew/bin/sketchybar --set cpu label=" ${CPU_USAGE}%"
else
    /opt/homebrew/bin/sketchybar --set cpu label="${CPU_USAGE}%"
fi
