#!/usr/bin/env python3

import subprocess
import sys
import time
from datetime import datetime
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

MANAGED_DEVICES = [
    ("WH-1000XM3", "38:18:4C:AE:2B:E3"),
    ("Google Home Speaker", "48:D6:D5:90:F1:E0"),
]

RECONCILE_DEBOUNCE_MS = 2000
RECONCILE_INTERVAL_SEC = 30
STARTUP_DELAY_SEC = 5

reconcile_timer = None


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def notify(msg):
    try:
        subprocess.run(
            ["dunstify", "-a", "bluetooth", "-u", "low", "-t", "3000", msg],
            check=False,
            capture_output=True,
        )
    except Exception as e:
        log(f"Notification failed: {e}")


def bluetoothctl(*args):
    try:
        result = subprocess.run(
            ["bluetoothctl", *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout.strip()
    except Exception as e:
        log(f"bluetoothctl error: {e}")
        return ""


def is_connected(mac):
    info = bluetoothctl("info", mac)
    if not info:
        return False
    for line in info.splitlines():
        if "Connected:" in line:
            parts = line.strip().split(":", 1)
            if len(parts) > 1:
                connected = parts[1].strip().lower()
                return connected == "yes"
    return False


def is_available(mac):
    """Device is available if it's connected OR has RSSI (in range)"""
    info = bluetoothctl("info", mac)
    if not info:
        return False

    has_rssi = False
    is_conn = False

    for line in info.splitlines():
        if "Connected:" in line:
            parts = line.strip().split(":", 1)
            if len(parts) > 1:
                is_conn = parts[1].strip().lower() == "yes"
        if "RSSI:" in line:
            has_rssi = True

    return is_conn or has_rssi


def connect_with_retries(mac, retries=3, delay=2):
    for attempt in range(1, retries + 1):
        log(f"Connecting to {mac} (attempt {attempt}/{retries})...")
        output = bluetoothctl("connect", mac)
        if "Connection successful" in output or is_connected(mac):
            return True
        if attempt < retries:
            time.sleep(delay)
    return False


def disconnect(mac):
    log(f"Disconnecting {mac}...")
    bluetoothctl("disconnect", mac)


def get_wpctl_status():
    """Get wpctl status output"""
    try:
        result = subprocess.run(
            ["wpctl", "status"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        return result.stdout
    except Exception as e:
        log(f"wpctl status error: {e}")
        return ""


def find_audio_sink(device_name, mac):
    """Find PipeWire audio sink node ID for a Bluetooth device"""
    status = get_wpctl_status()
    if not status:
        return None

    # Find the Sinks section
    lines = status.splitlines()
    in_sinks = False

    for line in lines:
        # Detect Sinks section
        if "Sinks:" in line:
            in_sinks = True
            continue

        # Exit Sinks section when we hit another top-level section
        if in_sinks and line.startswith(" ├─") and ":" in line:
            break

        # Parse sink lines: "  │      47. device_name [vol: 0.50]"
        # or with asterisk: "  │   *  52. other_device [vol: 0.75]"
        if in_sinks and ("│" in line):
            # Remove tree characters and asterisk
            cleaned = line.replace("│", "").replace("*", "").strip()

            # Extract node ID and name (format: "47. device_name [...]")
            if ". " in cleaned:
                parts = cleaned.split(". ", 1)
                if len(parts) == 2:
                    try:
                        node_id = int(parts[0].strip())
                        sink_name = parts[1].strip()

                        # Match by device name (case-insensitive)
                        if device_name.lower() in sink_name.lower():
                            log(f"  Found sink by name: ID {node_id}, name '{sink_name}'")
                            return node_id

                        # Match by MAC with underscores (e.g., "38_18_4C_AE_2B_E3")
                        mac_underscore = mac.replace(":", "_")
                        if mac_underscore in sink_name:
                            log(f"  Found sink by MAC: ID {node_id}, name '{sink_name}'")
                            return node_id
                    except (ValueError, IndexError):
                        continue

    return None


def set_default_sink(device_name, mac, retries=5, delay=2):
    """Set the default PipeWire audio sink for a Bluetooth device"""
    log(f"  Setting default audio sink for {device_name}...")

    for attempt in range(1, retries + 1):
        node_id = find_audio_sink(device_name, mac)

        if node_id is not None:
            try:
                result = subprocess.run(
                    ["wpctl", "set-default", str(node_id)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )

                if result.returncode == 0:
                    log(f"  Set default sink to {device_name} (node {node_id})")
                    notify(f"Audio output: {device_name}")
                    return True
                else:
                    log(f"  wpctl set-default failed: {result.stderr}")
            except Exception as e:
                log(f"  Error setting default sink: {e}")
        else:
            log(f"  Sink not found for {device_name} (attempt {attempt}/{retries})")

        if attempt < retries:
            time.sleep(delay)

    log(f"  Warning: Could not set default sink for {device_name} after {retries} attempts")
    return False


def reconcile():
    log("Running reconciliation...")

    connected = []
    for name, mac in MANAGED_DEVICES:
        if is_connected(mac):
            connected.append((name, mac))
            log(f"  {name} is connected")

    best_available = None
    for name, mac in MANAGED_DEVICES:
        if is_available(mac):
            best_available = (name, mac)
            log(f"  {name} is available (highest priority)")
            break

    if not best_available:
        log("  No managed devices available")
        return

    best_name, best_mac = best_available

    if is_connected(best_mac):
        log(f"  {best_name} is already connected (nothing to do)")
        # Still set default sink to ensure it's correct (handles manual changes)
        set_default_sink(best_name, best_mac)
        return

    for name, mac in connected:
        if mac != best_mac:
            log(f"  Lower priority device {name} is connected, disconnecting...")
            disconnect(mac)
            notify(f"Disconnected {name} for higher priority {best_name}")

    log(f"  Connecting to {best_name}...")
    success = connect_with_retries(best_mac, retries=3, delay=2)
    if success:
        log(f"  Successfully connected to {best_name}")
        notify(f"Connected to {best_name}")
        # Set default sink after successful connection
        set_default_sink(best_name, best_mac)
    else:
        log(f"  Failed to connect to {best_name}")

    # If we disconnected devices but connection failed, fall back to any remaining connected device
    if not success and connected:
        for name, mac in MANAGED_DEVICES:
            if is_connected(mac):
                log(f"  Falling back to {name}")
                set_default_sink(name, mac)
                break


def schedule_reconcile():
    global reconcile_timer

    if reconcile_timer is not None:
        GLib.source_remove(reconcile_timer)

    reconcile_timer = GLib.timeout_add(RECONCILE_DEBOUNCE_MS, debounced_reconcile)


def debounced_reconcile():
    global reconcile_timer
    reconcile_timer = None
    reconcile()
    return False


def periodic_reconcile():
    log("Periodic reconciliation triggered")
    reconcile()
    return True


def on_properties_changed(interface, changed, invalidated, path):
    if "org.bluez.Device1" not in interface:
        return

    if "Connected" in changed or "RSSI" in changed or "ServicesResolved" in changed:
        log(f"Device property changed on {path}")
        schedule_reconcile()


def main():
    log("Starting Bluetooth Audio Manager")
    log(f"Managed devices: {MANAGED_DEVICES}")

    DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    bus.add_signal_receiver(
        on_properties_changed,
        dbus_interface="org.freedesktop.DBus.Properties",
        signal_name="PropertiesChanged",
        path_keyword="path",
    )

    log("D-Bus signal monitoring started")

    GLib.timeout_add_seconds(STARTUP_DELAY_SEC, lambda: (reconcile(), False)[1])
    log(f"Initial reconciliation scheduled in {STARTUP_DELAY_SEC} seconds")

    GLib.timeout_add_seconds(RECONCILE_INTERVAL_SEC, periodic_reconcile)
    log(f"Periodic reconciliation every {RECONCILE_INTERVAL_SEC} seconds")

    loop = GLib.MainLoop()

    try:
        log("Entering main loop")
        loop.run()
    except KeyboardInterrupt:
        log("Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
