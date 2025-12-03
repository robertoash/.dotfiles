#!/usr/bin/env python3

import subprocess
import sys
import time

DEVICES = [
    ("WH-1000XM3", "AA:BB:CC:DD:EE:FF"),
    ("Google Home", "48:D6:D5:90:F1:E0"),
]

RETRIES = 3
SLEEP_BETWEEN = 1  # seconds


def notify(msg):
    subprocess.run(["dunstify", "-a", "bluetooth", "-u", "low", "-t", "2000", msg])


def bluetoothctl(*args):
    result = subprocess.run(["bluetoothctl", *args], capture_output=True, text=True)
    return result.stdout.strip()


def is_connected(mac):
    info = bluetoothctl("info", mac)
    if not info:
        return False
    for line in info.splitlines():
        if "Connected:" in line:
            connected = line.strip().split(":")[1].strip().lower()
            return connected == "yes"
    return False


def connect(mac):
    output = bluetoothctl("connect", mac)
    return "Connection successful" in output


def main():
    notify("🔵 Starting bluetooth autoconnect…")

    bluetoothctl("power", "on")

    for name, mac in DEVICES:
        if is_connected(mac):
            notify(f"✅ {name} already connected")
            return

        for attempt in range(1, RETRIES + 1):
            if connect(mac):
                notify(f"🎧 Connected to {name} (try {attempt})")
                return
            time.sleep(SLEEP_BETWEEN)

    notify("❌ Could not connect to any preferred device")
    sys.exit(1)


if __name__ == "__main__":
    main()
