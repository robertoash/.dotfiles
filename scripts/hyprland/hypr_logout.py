#!/usr/bin/env python3
import subprocess
import time


def graceful_shutdown():
    # Send SIGTERM to Brave for graceful shutdown
    subprocess.run(["pkill", "-15", "brave"])
    time.sleep(0.5)  # Optional: give Brave a moment to close

    # Logout of Hyprland
    subprocess.run(["hyprctl", "dispatch", "exit"])


if __name__ == "__main__":
    graceful_shutdown()
