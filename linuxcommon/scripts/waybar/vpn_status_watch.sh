#!/usr/bin/env bash
# Watch VPN status file with watchexec

STATUS_FILE="/tmp/waybar/vpn_status_output.json"

# Output initial state (echo adds the trailing newline the file lacks)
echo "$(cat "$STATUS_FILE" 2>/dev/null || echo '{"text":"?","class":"unknown","tooltip":"VPN status unknown"}')"

# Process substitution avoids subshell buffering issues
while read -r _; do
    echo "$(cat "$STATUS_FILE" 2>/dev/null || echo '{"text":"?","class":"unknown","tooltip":"VPN status unknown"}')"
done < <(watchexec --only-emit-events --watch "$STATUS_FILE")
