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

    profile_selector = "rofi_profile_selector"

    if len(sys.argv) > 1 and is_url(sys.argv[1]):
        url = sys.argv[1]
        if current_db == "rashp.db":
            subprocess.run(["mullvad-browser", url], check=False)
        else:
            subprocess.run([profile_selector, "qutebrowser", url], check=False)
    elif len(sys.argv) > 1:
        open_local_file(sys.argv[1])
    else:
        # No URL provided, just open browser
        subprocess.run([profile_selector, "qutebrowser"], check=False)


if __name__ == "__main__":
    main()
