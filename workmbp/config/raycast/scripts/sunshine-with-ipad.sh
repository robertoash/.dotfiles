#!/usr/bin/env bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Start Sunshine with iPad
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🎮
# @raycast.packageName Sunshine

# Documentation:
# @raycast.description Launch Sunshine with virtual iPad display
# @raycast.author rash

nohup /etc/profiles/per-user/rash/bin/sunshine-with-ipad > /tmp/sunshine-with-ipad.log 2>&1 &

echo "Started Sunshine with virtual iPad display"
