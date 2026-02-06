#!/usr/bin/env bash
# Watch in-office idle status file with watchexec

STATUS_FILE="/tmp/waybar/in_office_idle_output.json"

# Output initial state (echo adds the trailing newline the file lacks)
echo "$(cat "$STATUS_FILE" 2>/dev/null || echo '{"text":"?","class":"unknown","tooltip":"Status unknown"}')"

# Process substitution avoids subshell buffering issues
while read -r _; do
    echo "$(cat "$STATUS_FILE" 2>/dev/null || echo '{"text":"?","class":"unknown","tooltip":"Status unknown"}')"
done < <(watchexec --only-emit-events --watch "$STATUS_FILE")
