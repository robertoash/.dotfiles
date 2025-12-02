# Launch BetterDisplay if not running
if not pgrep -q BetterDisplay
  echo "Launching BetterDisplay..."
  open -g "/Applications/Nix Apps/BetterDisplay.app"
  sleep 3
end

# Create or reuse virtual display (stays connected, toggles mirror/extended)
set DISPLAY_NAME "iPad Virtual Display"
set DISPLAY_NAME_ENCODED "iPad%20Virtual%20Display"

# Check for existing display by name
set TAGID (curl -s "http://localhost:55777/get?identifiers" | grep -A 10 "$DISPLAY_NAME" | grep "tagID" | head -1 | grep -oE "[0-9]+" || echo "")

if test -z "$TAGID"
  echo "Creating persistent virtual display with 4:3 aspect ratio..."
  curl -s "http://localhost:55777/create?type=VirtualScreen&tagID=sunshine-ipad&virtualScreenName=$DISPLAY_NAME_ENCODED&aspectWidth=4&aspectHeight=3&virtualScreenHiDPI=off" >/dev/null
  sleep 1

  # Get the newly created display's tagID
  set TAGID (curl -s "http://localhost:55777/get?identifiers" | grep -A 10 "$DISPLAY_NAME" | grep "tagID" | head -1 | grep -oE "[0-9]+" || echo "")

  if test -n "$TAGID"
    echo "Configuring display settings (tagID: $TAGID)..."

    # Connect the display
    curl -s "http://localhost:55777/set?tagID=$TAGID&connected=on" >/dev/null
    sleep 1
    # Make iPad Virtual Display mirror L32p-30 (so virtual display shows L32p-30 content without taking desktop space)
    curl -s "http://localhost:55777/set?name=L32p-30&mirror=on&targetName=$DISPLAY_NAME_ENCODED" >/dev/null
  end
else
  echo "Found existing virtual display (tagID: $TAGID)"
  # Ensure it's connected and in mirror mode
  curl -s "http://localhost:55777/set?tagID=$TAGID&connected=on" >/dev/null
  sleep 1
  curl -s "http://localhost:55777/set?name=L32p-30&mirror=on&targetName=$DISPLAY_NAME_ENCODED" >/dev/null
  sleep 1
end

if test -n "$TAGID"
  # Get the macOS display ID and update sunshine.conf
  set DISPLAY_ID (curl -s "http://localhost:55777/get?identifiers" | grep -B 5 "$DISPLAY_NAME" | grep '"displayID"' | head -1 | grep -oE "[0-9]+" || echo "")

  if test -n "$DISPLAY_ID"
    echo "Virtual display ready (ID: $DISPLAY_ID, mode: mirror)"
    echo "Will switch to extended mode when client connects"
    sed -i '' "s/^output_name = .*/output_name = $DISPLAY_ID/" ~/.config/sunshine/sunshine.conf
  end
end

# No cleanup function - display stays persistent
# Setup signal traps (no cleanup needed)
trap "" SIGINT SIGTERM

# Start sunshine in foreground
/opt/homebrew/bin/sunshine
