#!/usr/bin/env bash
# Switch virtual display to extended mode and set resolution using displayplacer

LOG_FILE="/tmp/sunshine-ipad.log"
DISPLAY_NAME="iPad Virtual Display"

echo "=== Client Connecting ===" >> "$LOG_FILE"
echo "Client Resolution: ${SUNSHINE_CLIENT_WIDTH}x${SUNSHINE_CLIENT_HEIGHT} @ ${SUNSHINE_CLIENT_FPS}fps" >> "$LOG_FILE"

# Get the tagID, UUID, and display ID from BetterDisplay
TAGID=$(curl -s "http://localhost:55777/get?identifiers" | grep -A 10 "$DISPLAY_NAME" | grep "tagID" | head -1 | grep -oE "[0-9]+" || echo "")
DISPLAY_UUID=$(curl -s "http://localhost:55777/get?identifiers" | grep -B 5 "$DISPLAY_NAME" | grep '"UUID"' | head -1 | grep -oE "[A-F0-9-]{36}" || echo "")
DISPLAY_ID=$(curl -s "http://localhost:55777/get?identifiers" | grep -B 5 "$DISPLAY_NAME" | grep '"displayID"' | head -1 | grep -oE "[0-9]+" || echo "")

echo "TagID: $TAGID" >> "$LOG_FILE"
echo "UUID: $DISPLAY_UUID" >> "$LOG_FILE"
echo "Display ID: $DISPLAY_ID" >> "$LOG_FILE"

if [ -n "$TAGID" ]; then

  # Update sunshine.conf with the current display ID
  if [ -n "$DISPLAY_ID" ]; then
    sed -i '' "s/^output_name = .*/output_name = $DISPLAY_ID/" ~/.config/sunshine/sunshine.conf
    echo "Updated sunshine.conf with display ID: $DISPLAY_ID" >> "$LOG_FILE"
  fi

  # Switch to extended mode using BetterDisplay API
  echo "Switching to extended mode..." >> "$LOG_FILE"
  curl -s "http://localhost:55777/set?tagID=$TAGID&mirror=off" >> "$LOG_FILE" 2>&1

  # Set resolution and position using displayplacer
  # IMPORTANT: Must set ALL displays at once to maintain physical monitor positions
  if [ -n "$DISPLAY_UUID" ] && [ -n "$SUNSHINE_CLIENT_WIDTH" ] && [ -n "$SUNSHINE_CLIENT_HEIGHT" ]; then
    RESOLUTION="${SUNSHINE_CLIENT_WIDTH}x${SUNSHINE_CLIENT_HEIGHT}"
    HZ="${SUNSHINE_CLIENT_FPS:-60}"
    echo "Setting resolution to: $RESOLUTION @ ${HZ}Hz and maintaining physical monitor positions" >> "$LOG_FILE"

    # Set all 3 displays at once: L32p-30 (primary at 0,0), P27u-20 (left), iPad (to the right)
    /opt/homebrew/bin/displayplacer \
      "id:A9331109-1992-48A7-A4BC-378F446A3631 res:3008x1692 hz:60 color_depth:8 enabled:true scaling:on origin:(0,0) degree:0" \
      "id:7CE3B1E6-77B3-4709-BE56-79B3BF2ECBF7 res:1440x2560 hz:60 color_depth:8 enabled:true scaling:on origin:(-1440,-729) degree:90" \
      "id:$DISPLAY_UUID res:$RESOLUTION hz:$HZ color_depth:4 enabled:true scaling:off origin:(3008,1235) degree:0" \
      >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
      echo "All displays configured successfully" >> "$LOG_FILE"
    else
      echo "Warning: displayplacer failed, some display settings may not have applied" >> "$LOG_FILE"
    fi
  elif [ -z "$DISPLAY_UUID" ]; then
    echo "ERROR: Could not get UUID from BetterDisplay" >> "$LOG_FILE"
  fi

  echo "Display configured for streaming" >> "$LOG_FILE"
else
  echo "ERROR: Could not find display" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
exit 0
