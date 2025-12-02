#!/usr/bin/env bash
# Create and connect iPad Virtual Display for Sunshine streaming

DISPLAY_NAME="iPad Virtual Display"
DISPLAY_NAME_ENCODED="iPad%20Virtual%20Display"
# Default resolution matching Hyprland setup: 1280x960@60 (no HiDPI)
RESOLUTIONS="1280x960,1920x1440,2048x1536"
DEFAULT_RESOLUTION="1280x960"

# Check if BetterDisplay is running, launch if not
if ! pgrep -q BetterDisplay; then
    open -g "/Applications/Nix Apps/BetterDisplay.app"
    sleep 3
fi

# Check if display already exists
if curl -s "http://localhost:55777/get?identifiers" | grep -q "$DISPLAY_NAME"; then
    echo "Virtual display already exists"
else
    echo "Creating virtual display..."
    curl -s "http://localhost:55777/create?type=VirtualScreen&tagID=sunshine-ipad&virtualScreenName=${DISPLAY_NAME_ENCODED}&resolutionList=$RESOLUTIONS&virtualScreenHiDPI=off" >/dev/null
fi

# Get the tagID and connect the display
TAGID=$(curl -s "http://localhost:55777/get?identifiers" | grep -A 10 "$DISPLAY_NAME" | grep "tagID" | head -1 | grep -oE "[0-9]+" || echo "")

if [ -n "$TAGID" ]; then
    echo "Connecting display with tagID $TAGID..."
    curl -s "http://localhost:55777/set?tagID=$TAGID&connected=on" >/dev/null
    sleep 2

    # Get the macOS display ID
    DISPLAY_ID=$(curl -s "http://localhost:55777/get?identifiers" | grep -B 5 "$DISPLAY_NAME" | grep '"displayID"' | head -1 | grep -oE "[0-9]+" || echo "")

    if [ -n "$DISPLAY_ID" ]; then
        # Set the virtual display to use the default resolution
        curl -s "http://localhost:55777/set?tagID=$TAGID&resolution=$DEFAULT_RESOLUTION" >/dev/null

        # Update sunshine.conf with the new display ID
        SUNSHINE_CONF="$HOME/.config/sunshine/sunshine.conf"
        if [ -f "$SUNSHINE_CONF" ]; then
            # Update or add output_name in sunshine.conf
            if grep -q "^output_name = " "$SUNSHINE_CONF"; then
                sed -i '' "s/^output_name = .*/output_name = $DISPLAY_ID/" "$SUNSHINE_CONF"
            else
                # Add output_name after the comment about not setting it globally
                sed -i '' "/^# Don't set a global output_name/a\\
output_name = $DISPLAY_ID
" "$SUNSHINE_CONF"
            fi
            echo "Virtual display ready (ID: $DISPLAY_ID, resolution: $DEFAULT_RESOLUTION)"
        else
            echo "Virtual display ready (ID: $DISPLAY_ID)"
        fi
    else
        echo "Virtual display ready (could not get display ID)"
    fi
else
    echo "Warning: Could not find display tagID, display may already be connected"
fi

exit 0
