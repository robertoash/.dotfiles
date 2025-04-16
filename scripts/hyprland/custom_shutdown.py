#!/usr/bin/env python3

import subprocess
import sys
import time

# List of apps to gracefully quit
APPS_TO_QUIT = ["vivaldi"]

# How long to wait (in seconds) for apps to close gracefully
WAIT_SECONDS = 0.5


def terminate_apps():
    for app in APPS_TO_QUIT:
        print(f"Terminating {app} gracefully...")
        subprocess.run(["pkill", "-15", app])  # Send SIGTERM
    print(f"Waiting {WAIT_SECONDS} seconds for apps to close gracefully...")
    time.sleep(WAIT_SECONDS)


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ["--logout", "--reboot", "--poweroff"]:
        print("Usage: custom_shutdown.py {--logout|--reboot|--poweroff}")
        sys.exit(1)

    action = sys.argv[1]

    terminate_apps()

    if action == "--logout":
        print("Logging out...")
        subprocess.run(["hyprctl", "dispatch", "exit"])
    elif action == "--reboot":
        print("Rebooting system...")
        subprocess.run(["systemctl", "reboot"])
    elif action == "--poweroff":
        print("Powering off system...")
        subprocess.run(["systemctl", "poweroff"])


if __name__ == "__main__":
    main()
