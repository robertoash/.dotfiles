#!/usr/bin/env bash
# Watch kanata status file with watchexec
# watchexec emits events, we cat on each event

STATUS_FILE="/tmp/kanata_status.json"

# Output initial state (echo adds the trailing newline the file lacks)
echo "$(cat "$STATUS_FILE")"

# Process substitution avoids subshell buffering issues
while read -r _; do
    echo "$(cat "$STATUS_FILE")"
done < <(watchexec --only-emit-events --watch "$STATUS_FILE")
