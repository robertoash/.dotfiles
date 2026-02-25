#!/usr/bin/env bash
# Watch VPN status file with watchexec

STATUS_FILE="/tmp/waybar/vpn_status_output.json"
STATUS_DIR="$(dirname "$STATUS_FILE")"
UNKNOWN='{"text":"?","class":"unknown","tooltip":"VPN status unknown"}'

mkdir -p "$STATUS_DIR"

# Output initial state (echo adds the trailing newline the file lacks)
echo "$(cat "$STATUS_FILE" 2>/dev/null || echo "$UNKNOWN")"

# Watch the directory so we detect file creation, not just modification.
# This handles the case where the file doesn't exist yet at boot.
while read -r _; do
    echo "$(cat "$STATUS_FILE" 2>/dev/null || echo "$UNKNOWN")"
done < <(watchexec --only-emit-events --watch "$STATUS_DIR")
