#!/usr/bin/env python3
import os
import subprocess
import time

# Path to the image
image_path = "/home/rash/pictures/cheatsheets/qutebrowser_cheatsheet.png"

# PID file to track the feh process
pid_file = "/tmp/quicklook_qutebrowser_cheatsheet.pid"


def toggle_image():
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
            try:
                os.kill(pid, 0)  # Check if the process is running
                os.kill(pid, 9)  # Kill it
                os.waitpid(pid, 0)  # Wait for the process to terminate
                os.remove(pid_file)  # Remove PID file after killing the process
                return
            except OSError:
                os.remove(pid_file)  # Remove PID file if the process is not running
    else:
        # If the process is not running, start it
        process = subprocess.Popen(
            [
                "feh",
                "--fullscreen",
                "--auto-zoom",
                "--min-zoom",
                "50",
                "--title",
                "quicklook_qutebrowser_cheatsheet",
                image_path,
            ]
        )

        with open(pid_file, "w") as f:
            f.write(str(process.pid))


if __name__ == "__main__":
    toggle_image()
