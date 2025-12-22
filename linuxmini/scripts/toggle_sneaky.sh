#!/usr/bin/env bash
#
# Toggle sneaky mode - tags floating window and starts/stops monitor systemd service
#

SERVICE_NAME="sneaky-window-monitor.service"

# Check if monitor service is running
if systemctl --user is-active --quiet "$SERVICE_NAME"; then
    # Service is running - stop it and remove sneaky tags
    echo "Stopping sneaky monitor service..."
    systemctl --user stop "$SERVICE_NAME"

    # Get all sneaky windows (need to do this before removing tags)
    sneaky_windows=$(hyprctl clients -j | python3 -c "
import sys, json
clients = json.load(sys.stdin)
sneaky = [c['address'] for c in clients if 'sneaky' in c.get('tags', [])]
print(' '.join(sneaky))
")

    # Remove sneaky tags and composite tags (don't modify window state)
    for address in $sneaky_windows; do
        hyprctl dispatch tagwindow -- -sneaky "address:$address" > /dev/null 2>&1
        # Also remove composite tags that Hyprland might have created
        hyprctl dispatch tagwindow -- -sneaky_unfocused "address:$address" > /dev/null 2>&1
        hyprctl dispatch tagwindow -- -sneaky_focused "address:$address" > /dev/null 2>&1
    done

    # Reload Hyprland to refresh window rules and borders
    hyprctl reload > /dev/null 2>&1

    notify-send "Sneaky Mode" "Disabled" -t 2000
    exit 0
fi

# Service is not running - tag window and start service
echo "Starting sneaky monitor service..."

# Toggle sneaky tag using hypr-window-ops (DRY - reuses smart targeting logic)
hypr-window-ops toggle-sneaky --relative-floating

# Start monitor service
systemctl --user start "$SERVICE_NAME"

notify-send "Sneaky Mode" "Enabled" -t 2000

exit 0
