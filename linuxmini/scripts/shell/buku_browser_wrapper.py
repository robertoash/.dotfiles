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

    # Get the profile name from a shorter basedir to avoid line length issues
    home = Path.home()
    qute_profile = f"{home}/.local/bin/qute_profile"
    profile_name = "rash"
    qute_basedir = f"{home}/.config/qutebrowser/profiles/{profile_name}"

    if called_by_buku:
        if len(sys.argv) > 1 and is_url(sys.argv[1]):
            url = sys.argv[1]
            if current_db == "rashp.db":
                subprocess.run(["mullvad-browser", url], check=False)
            else:
                try:
                    # Check if qutebrowser with rash profile is already running
                    qb_process = subprocess.run(
                        ["pgrep", "-f", f"qutebrowser.*{profile_name}"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if qb_process.returncode == 0:
                        # Use target=tab to open URLs in a new tab
                        subprocess.run(
                            [
                                "qutebrowser",
                                "--target=tab",
                                f"--basedir={qute_basedir}",
                                url,
                            ],
                            check=False,
                        )
                    else:
                        # Start new instance with URL
                        subprocess.run([qute_profile, profile_name, url], check=False)
                except Exception:
                    # Fallback - use profile directly passing all args
                    subprocess.run([qute_profile, profile_name, url], check=False)
        else:
            open_local_file(sys.argv[1])
    else:
        if len(sys.argv) > 1 and is_url(sys.argv[1]):
            url = sys.argv[1]
            try:
                # Check if qutebrowser with rash profile is already running
                qb_process = subprocess.run(
                    ["pgrep", "-f", f"qutebrowser.*{profile_name}"],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if qb_process.returncode == 0:
                    # Use target=tab to open URLs in a new tab
                    subprocess.run(
                        [
                            "qutebrowser",
                            "--target=tab",
                            f"--basedir={qute_basedir}",
                            url,
                        ],
                        check=False,
                    )
                else:
                    # Start new instance with URL
                    subprocess.run([qute_profile, profile_name, url], check=False)
            except Exception:
                # Fallback - use profile directly passing all args
                subprocess.run([qute_profile, profile_name, url], check=False)
        else:
            # No URL provided, just open browser
            subprocess.run([qute_profile, profile_name], check=False)


if __name__ == "__main__":
    main()
