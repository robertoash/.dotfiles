#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path


def is_url(url):
    return url.startswith(("http://", "https://"))


def open_local_file(file):
    subprocess.run(["xdg-open", file])


def main():
    db_dir = Path.home() / ".local" / "share" / "buku"
    current_db_file = db_dir / "current_db.txt"

    try:
        with open(current_db_file, "r") as f:
            current_db = f.read().strip()
    except FileNotFoundError:
        current_db = "rash.db"  # Default value if file doesn't exist

    # Check if the script was called by buku
    parent_process = subprocess.run(
        ["ps", "-o", "command=", "-p", str(os.getppid())],
        capture_output=True,
        text=True,
    ).stdout.strip()
    called_by_buku = "buku" in parent_process

    if called_by_buku:
        if len(sys.argv) > 1 and is_url(sys.argv[1]):
            if current_db == "rashp.db":
                subprocess.run(["mullvad-browser"] + sys.argv[1:])
            else:
                original_browser = os.environ.get("ORIGINAL_BROWSER", "vivaldi")
                subprocess.run([original_browser] + sys.argv[1:])
        else:
            open_local_file(sys.argv[1])
    else:
        original_browser = os.environ.get("ORIGINAL_BROWSER", "vivaldi")
        subprocess.run([original_browser] + sys.argv[1:])


if __name__ == "__main__":
    main()
