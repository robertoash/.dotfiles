#!/bin/bash

# Monitor for Kanata restarts and restart espanso when detected
# Uses the kanata process PID as a proxy for restarts

LAST_KANATA_PID=""
CHECK_INTERVAL=5

get_kanata_pid() {
    pgrep -x kanata | head -1
}

echo "$(date): Starting espanso input monitor"

while true; do
    CURRENT_KANATA_PID=$(get_kanata_pid)
    
    if [ -n "$CURRENT_KANATA_PID" ]; then
        if [ -n "$LAST_KANATA_PID" ] && [ "$LAST_KANATA_PID" != "$CURRENT_KANATA_PID" ]; then
            echo "$(date): Kanata restarted (PID changed: $LAST_KANATA_PID -> $CURRENT_KANATA_PID)"
            echo "$(date): Waiting 2 seconds for Kanata to stabilize..."
            sleep 2
            echo "$(date): Restarting espanso..."
            systemctl --user restart espanso.service
            echo "$(date): Espanso restarted"
        fi
        LAST_KANATA_PID="$CURRENT_KANATA_PID"
    fi
    
    sleep $CHECK_INTERVAL
done