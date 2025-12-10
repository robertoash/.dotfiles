#!/usr/bin/env bash
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
BT_STATUS=$(defaults read /Library/Preferences/com.apple.Bluetooth ControllerPowerState 2>/dev/null)
if [ "$BT_STATUS" = "1" ]; then
    # Bluetooth is ON, check for connected devices
    BT_DEVICES=$(system_profiler SPBluetoothDataType 2>/dev/null | grep -c "Connected: Yes")
    if [ "$BT_DEVICES" -gt 0 ]; then
        # Connected
        /opt/homebrew/bin/sketchybar --set bluetooth icon="󰂱"
    else
        # On but not connected
        /opt/homebrew/bin/sketchybar --set bluetooth icon="󰂯"
    fi
else
    # Bluetooth is OFF
    /opt/homebrew/bin/sketchybar --set bluetooth icon="󰂲"
fi
