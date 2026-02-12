---
phase: quick-7
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - linuxmini/scripts/hyprland/bluetooth_audio_manager.py
  - linuxmini/systemd/user/bluetooth-audio-manager.service
  - linuxmini/config/hypr/keybinds.conf
autonomous: true
must_haves:
  truths:
    - "When WH-1000XM3 becomes available, it auto-connects (highest priority)"
    - "When Google Home Speaker becomes available and WH-1000XM3 is not connected, it auto-connects"
    - "When WH-1000XM3 appears while Google Home Speaker is connected, GHS is disconnected and WH connects"
    - "When WH-1000XM3 is connected and Google Home Speaker appears, nothing changes"
    - "Other Bluetooth devices (phone, etc.) are not affected by the manager"
    - "The service starts automatically on login and runs continuously"
  artifacts:
    - path: "linuxmini/scripts/hyprland/bluetooth_audio_manager.py"
      provides: "Priority-based Bluetooth audio connection daemon"
    - path: "linuxmini/systemd/user/bluetooth-audio-manager.service"
      provides: "Systemd user service for the daemon"
  key_links:
    - from: "bluetooth-audio-manager.service"
      to: "bluetooth_audio_manager.py"
      via: "ExecStart"
    - from: "bluetooth_audio_manager.py"
      to: "org.bluez D-Bus interface"
      via: "D-Bus signal monitoring for PropertiesChanged"
---

<objective>
Replace the manual SUPER+SHIFT+B bluetooth autoconnect keybind with an automated priority-based
Bluetooth audio device manager that runs as a systemd user service.

Purpose: Eliminate manual bluetooth connection management by automatically connecting to
the highest-priority available audio device (WH-1000XM3 > Google Home Speaker).

Output: A running daemon + systemd service that monitors bluetooth device availability via
D-Bus and manages connections with priority logic.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@linuxmini/scripts/hyprland/bluetooth_autoconnect.py
@linuxmini/config/hypr/keybinds.conf
@linuxmini/systemd/user/sneaky-window-monitor.service
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create priority-based Bluetooth audio manager daemon</name>
  <files>linuxmini/scripts/hyprland/bluetooth_audio_manager.py</files>
  <action>
Create a Python daemon that monitors Bluetooth device state via D-Bus and manages audio
device connections with priority logic.

**Device priority list (highest first):**
1. WH-1000XM3 -- MAC: 38:18:4C:AE:2B:E3
2. Google Home Speaker -- MAC: 48:D6:D5:90:F1:E0

**Implementation approach -- D-Bus event-driven with periodic reconciliation:**

Use `dbus` and `gi.repository.GLib` (both already available on the system) to listen for
`org.freedesktop.DBus.Properties.PropertiesChanged` signals on the `org.bluez` bus.
This catches device connected/disconnected/RSSI-appeared events without polling.

Add a GLib timeout (every 30 seconds) as a reconciliation fallback to handle any missed
events (e.g., if the daemon starts while a device is already available but not connected).

**Core logic (the `reconcile()` function, called on events AND periodically):**

```
managed_devices = [("WH-1000XM3", "38:18:4C:AE:2B:E3"), ("Google Home Speaker", "48:D6:D5:90:F1:E0")]

def reconcile():
    # 1. Check which managed devices are currently connected
    connected = [dev for dev in managed_devices if is_connected(dev.mac)]

    # 2. Find highest-priority device that is available (paired + in range)
    #    Use bluetoothctl info to check if device is available (has RSSI or is connected)
    best_available = None
    for dev in managed_devices:  # already in priority order
        if is_available(dev.mac):
            best_available = dev
            break

    # 3. If nothing available, do nothing
    if not best_available:
        return

    # 4. If best available is already connected, done
    if is_connected(best_available.mac):
        return

    # 5. If a lower-priority managed device is connected, disconnect it
    for dev in connected:
        if dev != best_available:
            disconnect(dev.mac)
            notify(f"Disconnected {dev.name} for higher priority {best_available.name}")

    # 6. Connect to best available
    success = connect_with_retries(best_available.mac, retries=3, delay=2)
    if success:
        notify(f"Connected to {best_available.name}")
    else:
        log(f"Failed to connect to {best_available.name}")
```

**Helper functions:**
- `is_connected(mac)`: Run `bluetoothctl info {mac}`, parse "Connected: yes/no"
- `is_available(mac)`: Run `bluetoothctl info {mac}`, check device exists AND (Connected: yes OR RSSI exists).
  RSSI presence in `bluetoothctl info` indicates the device is in range. If no RSSI line and not
  connected, the device is not available.
- `connect_with_retries(mac, retries, delay)`: Attempt `bluetoothctl connect {mac}` up to N times,
  check for "Connection successful" in output
- `disconnect(mac)`: Run `bluetoothctl disconnect {mac}`
- `notify(msg)`: Use `dunstify -a "bluetooth" -u low -t 3000 msg`

**D-Bus signal handler:**
- Listen on system bus for `org.freedesktop.DBus.Properties.PropertiesChanged` with interface
  `org.bluez.Device1`. When properties like `Connected`, `RSSI`, or `ServicesResolved` change
  for any device, call `reconcile()` (with a short debounce of ~2 seconds via GLib.timeout_add
  to avoid rapid-fire reconnection attempts).

**Important details:**
- Add a debounce mechanism: when an event fires, schedule reconcile in 2 seconds. If another
  event fires before that, reset the timer. This prevents thrashing during connect/disconnect
  sequences.
- Only manage the two listed devices. The script must NEVER disconnect or interfere with any
  device not in the managed_devices list.
- Use `#!/usr/bin/env python3` shebang, make executable.
- Log to stdout (journald will capture via systemd). Use a simple `log()` function that
  prints with timestamps.
- On startup, run an initial `reconcile()` after a 5-second delay (via GLib.timeout_add)
  to handle the case where the service starts and devices are already available.

**Do NOT:**
- Import asyncio (use GLib mainloop instead, matches system availability)
- Use `bluetoothctl monitor` subprocess (flaky, use D-Bus directly)
- Touch non-managed Bluetooth devices in any way
  </action>
  <verify>
Run: `python3 linuxmini/scripts/hyprland/bluetooth_audio_manager.py --help` or just syntax check
with `python3 -c "import ast; ast.parse(open('linuxmini/scripts/hyprland/bluetooth_audio_manager.py').read())"`.
Verify the script has the correct MAC addresses (38:18:4C:AE:2B:E3 and 48:D6:D5:90:F1:E0),
uses D-Bus for event monitoring, and implements the priority reconciliation logic.
  </verify>
  <done>
bluetooth_audio_manager.py exists, is executable, contains correct MAC addresses for both devices,
implements D-Bus property change monitoring with GLib mainloop, has priority-based reconcile logic,
and only manages the two specified devices.
  </done>
</task>

<task type="auto">
  <name>Task 2: Create systemd service and update keybinds</name>
  <files>
    linuxmini/systemd/user/bluetooth-audio-manager.service
    linuxmini/config/hypr/keybinds.conf
  </files>
  <action>
**Part A: Create the systemd user service file.**

Create `linuxmini/systemd/user/bluetooth-audio-manager.service` following the pattern of
`sneaky-window-monitor.service` (simple long-running daemon, no network dependency needed
since bluetooth is local):

```ini
[Unit]
Description=Priority-based Bluetooth Audio Device Manager
After=bluetooth.target
Wants=bluetooth.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -u /home/rash/.dotfiles/linuxmini/scripts/hyprland/bluetooth_audio_manager.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
```

Note: ExecStart points to the dotfiles source directly (like sneaky-window-monitor.service does),
NOT to the symlinked ~/.config path. RestartSec=10 since bluetooth devices appearing/disappearing
is not time-critical and we want to avoid restart storms.

**Part B: Update keybinds.conf.**

In `linuxmini/config/hypr/keybinds.conf`, change line 69 from:
```
bindd = SUPER SHIFT, B, Autoconnect bluetooth, exec, ~/.config/scripts/hyprland/bluetooth_autoconnect.py
```
to:
```
bindd = SUPER SHIFT, B, Restart bluetooth audio manager, exec, systemctl --user restart bluetooth-audio-manager.service
```

This repurposes the keybind as a manual "kick" to restart the service if something goes wrong,
rather than the old one-shot connect script. The description changes to reflect the new behavior.

**Part C: Run setup.py and enable the service.**

After creating both files:
1. Run `cd /home/rash/.dotfiles && python setup.py` to deploy symlinks
2. Run `systemctl --user daemon-reload`
3. Run `systemctl --user enable bluetooth-audio-manager.service`
4. Run `systemctl --user start bluetooth-audio-manager.service`
5. Check status with `systemctl --user status bluetooth-audio-manager.service`
6. Check initial logs with `journalctl --user -u bluetooth-audio-manager.service --no-pager -n 20`

Do NOT delete the old `bluetooth_autoconnect.py` file -- leave it in place for reference. It is
not referenced by anything once the keybind is updated.
  </action>
  <verify>
Run:
- `systemctl --user is-enabled bluetooth-audio-manager.service` should return "enabled"
- `systemctl --user is-active bluetooth-audio-manager.service` should return "active"
- `journalctl --user -u bluetooth-audio-manager.service --no-pager -n 20` should show startup logs
  and initial reconciliation attempt
- `grep "SUPER SHIFT, B" linuxmini/config/hypr/keybinds.conf` should show the new restart command
  </verify>
  <done>
The bluetooth-audio-manager systemd service is enabled and running. The SUPER+SHIFT+B keybind
now restarts the service instead of running the old one-shot script. Logs show the daemon started
and performed initial device reconciliation.
  </done>
</task>

</tasks>

<verification>
1. Service is running: `systemctl --user is-active bluetooth-audio-manager.service` returns "active"
2. Logs show D-Bus monitoring started: `journalctl --user -u bluetooth-audio-manager -n 30 --no-pager`
3. Current bluetooth state is correct: if Google Home Speaker was connected, it should still be
   connected (it's the best available since WH-1000XM3 is not in range based on current state)
4. Keybind updated: `grep "bluetooth-audio-manager" linuxmini/config/hypr/keybinds.conf` matches
5. No interference with other BT devices: `bluetoothctl devices` shows all devices unchanged
</verification>

<success_criteria>
- bluetooth_audio_manager.py daemon runs continuously, monitoring D-Bus for bluetooth device changes
- Systemd service is enabled and active, will auto-start on login
- Priority logic works: WH-1000XM3 always takes precedence over Google Home Speaker
- Non-managed bluetooth devices are never touched
- SUPER+SHIFT+B keybind repurposed to restart the service
</success_criteria>

<output>
After completion, create `.planning/quick/7-implement-priority-based-bluetooth-audio/7-SUMMARY.md`
</output>
