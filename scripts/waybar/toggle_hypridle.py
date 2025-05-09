#!/usr/bin/env python3
import argparse
import os
import signal
import subprocess
from pathlib import Path

PID_FILE = Path("/tmp/waybar/hypridle.pid")
STATUS_FILE = Path("/tmp/waybar/hypridle_status.json")


def write_status(hypridle_is_on: bool):
    # ⚫ = running, 🔴 = off: because we want to show idle_inhibit status in waybar
    STATUS_FILE.write_text("⚫" if hypridle_is_on else "🔴")


def get_status():
    if PID_FILE.exists():
        return True
    else:
        return False


def toggle_hypridle(hypridle_is_on: bool):
    if hypridle_is_on:
        try:
            os.kill(int(PID_FILE.read_text()), signal.SIGTERM)
        except ProcessLookupError:
            pass
        PID_FILE.unlink(missing_ok=True)
        return False
    else:
        proc = subprocess.Popen(
            ["hypridle"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        PID_FILE.write_text(str(proc.pid))
        return True


def main():
    parser = argparse.ArgumentParser(description="Toggle hypridle on/off")
    parser.add_argument(
        "--start-fresh",
        action="store_true",
        help="Delete PID file if it exists and turn hypridle on",
    )
    args = parser.parse_args()

    if args.start_fresh:
        PID_FILE.unlink(missing_ok=True)
        hypridle_is_on = False
    else:
        hypridle_is_on = get_status()

    hypridle_is_on = toggle_hypridle(hypridle_is_on)
    write_status(hypridle_is_on)


if __name__ == "__main__":
    main()
