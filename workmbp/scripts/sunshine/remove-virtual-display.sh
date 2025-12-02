#!/usr/bin/env bash
# Switch iPad Virtual Display back to mirror mode after streaming

LOG_FILE="/tmp/sunshine-ipad.log"
DISPLAY_NAME="iPad Virtual Display"

echo "=== Client Disconnecting ===" >> "$LOG_FILE"

# Get the tagID of the virtual display
TAGID=$(curl -s "http://localhost:55777/get?identifiers" | grep -A 10 "$DISPLAY_NAME" | grep "tagID" | head -1 | grep -oE "[0-9]+" || echo "")

if [ -n "$TAGID" ]; then
  echo "Switching back to mirror mode (tagID: $TAGID)..." >> "$LOG_FILE"
  # Make iPad Virtual Display mirror L32p-30 again
  DISPLAY_NAME_ENCODED="iPad%20Virtual%20Display"
  curl -s "http://localhost:55777/set?name=L32p-30&mirror=on&targetName=$DISPLAY_NAME_ENCODED" >> "$LOG_FILE" 2>&1
  echo "iPad Virtual Display now mirroring L32p-30" >> "$LOG_FILE"
else
  echo "WARNING: Display not found" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
exit 0
