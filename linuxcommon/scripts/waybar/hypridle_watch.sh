#!/usr/bin/env bash
# Watch hypridle status file with watchexec

STATUS_FILE="/tmp/waybar/idle_status.json"

# Output initial state
echo "$(jq -r '.text // "⚫"' "$STATUS_FILE" 2>/dev/null || echo '⚫')"

# Process substitution avoids subshell buffering issues
while read -r _; do
    echo "$(jq -r '.text // "⚫"' "$STATUS_FILE" 2>/dev/null || echo '⚫')"
done < <(watchexec --only-emit-events --watch "$STATUS_FILE")
