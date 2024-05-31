#!/usr/bin/env python3
import os
import subprocess

# Path to the image
image_path = "http://10.20.10.50:8999/elpris.png"

# PID file to track the feh process
pid_file = "/tmp/quicklook_elpris.pid"


def toggle_image():
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
            try:
                os.kill(pid, 0)  # Check if the process is running
                os.kill(pid, 9)  # Kill it
                os.remove(pid_file)
                return
            except OSError:
                os.remove(pid_file)

    # Open the image with feh in a floating window mode
    process = subprocess.Popen(
        [
            "feh",
            "--fullscreen",
            "--auto-zoom",
            "--zoom",
            "125",
            "--title",
            "quicklook_elpris",
            image_path,
        ]
    )

    with open(pid_file, "w") as f:
        f.write(str(process.pid))


if __name__ == "__main__":
    toggle_image()
