#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Stop Sunshine with iPad
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🛑
# @raycast.packageName Sunshine

# Documentation:
# @raycast.description Stop Sunshine and remove virtual iPad display
# @raycast.author rash

# Find and kill the sunshine process (not sunshine-with-ipad wrapper)
pkill -TERM sunshine

# Clean up virtual display if it still exists
TAGID=$(curl -s "http://localhost:55777/get?identifiers" | grep -A 10 "iPad Virtual Display" | grep "tagID" | head -1 | grep -oE "[0-9]+" || echo "")
if [ -n "$TAGID" ]; then
  curl -s "http://localhost:55777/discard?type=VirtualScreen&tagID=$TAGID" >/dev/null
fi

echo "Stopped Sunshine and removed virtual display"
