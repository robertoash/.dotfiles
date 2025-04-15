#!/usr/bin/env python3
import argparse
import select
import signal
import sys
from glob import glob

from evdev import InputDevice, ecodes

DEFAULT_EXIT_AFTER = 15


def is_keyboard(dev):
    try:
        return ecodes.EV_KEY in dev.capabilities()
    except Exception as e:
        print(f"❌ Error checking {dev.path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Identify which input device sends key events."
    )
    parser.add_argument(
        "--grab", action="store_true", help="Grab devices (⚠️ blocks input!)"
    )
    parser.add_argument(
        "--loop", action="store_true", help="Don't exit after first keypress"
    )
    parser.add_argument(
        "--exit-after", type=int, default=15, help="Exit after N seconds (default: 15)"
    )
    args = parser.parse_args()

    signal.signal(signal.SIGALRM, lambda *_: sys.exit(0))

    if args.exit_after:
        # Respect explicit timeout
        signal.alarm(args.exit_after)
    elif not args.loop:
        # Default timeout for non-loop mode
        signal.alarm(DEFAULT_EXIT_AFTER)

    devices = []
    print("🔍 Scanning /dev/input/event* ...")
    for path in glob("/dev/input/event*"):
        try:
            dev = InputDevice(path)
            if is_keyboard(dev):
                if args.grab:
                    dev.grab()
                devices.append(dev)
                print(f"👂 Listening on {path}: {dev.name}")
        except Exception as e:
            print(f"❌ Skipping {path}: {e}")

    if not devices:
        print("🚫 No keyboard devices found.")
        return

    print(
        f"🚀 Press keys to identify source devices (timeout: {args.exit_after}s)...\n"
    )

    while True:
        r, _, _ = select.select(devices, [], [])
        for dev in r:
            for event in dev.read():
                if event.type == ecodes.EV_KEY and event.value == 1:
                    key = ecodes.KEY.get(event.code, f"Unknown({event.code})")
                    print("📨 Keypress detected:")
                    print(f"  🛠  Device: {dev.path}")
                    print(f"  🧾  Name:   {dev.name}")
                    print(f"  🔢  Key:    {key} (code {event.code})\n")
                    if not args.loop:
                        return


if __name__ == "__main__":
    main()
