#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path


def cheatsheet_config(name, image_path, zoom=None):
    pid_file = (
        f"/tmp/quicklook_{name}_cheatsheet.pid"
        if name != "elpris"
        else "/tmp/quicklook_elpris.pid"
    )
    title = f"quicklook_{name}_cheatsheet" if name != "elpris" else "quicklook_elpris"
    feh_args = ["--fullscreen", "--auto-zoom"]
    if zoom is not None:
        feh_args += ["--zoom", str(zoom)]
    feh_args += ["--title", title]
    return {
        "image_path": image_path,
        "pid_file": pid_file,
        "feh_args": feh_args,
    }


CHEATSHEET_DIR = Path("/home/rash/images/cheatsheets")
ELPRIS_URL = "http://10.20.10.50:8999/elpris.png"

# Cheatsheet configuration mapping (concise)
CHEATSHEETS = {
    "elpris": cheatsheet_config("elpris", ELPRIS_URL, zoom=200),
    "nvim": cheatsheet_config("nvim", CHEATSHEET_DIR / "nvim_cheatsheet.png"),
    "vim": cheatsheet_config("vim", CHEATSHEET_DIR / "vim_cheatsheet.png"),
    "qutebrowser": cheatsheet_config(
        "qutebrowser", CHEATSHEET_DIR / "qutebrowser_cheatsheet.png"
    ),
}


def toggle_image(config):
    pid_file = config["pid_file"]
    image_path = config["image_path"]
    feh_args = config["feh_args"]

    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
            try:
                os.kill(pid, 0)
                os.kill(pid, 9)
                try:
                    os.waitpid(pid, 0)
                except ChildProcessError:
                    pass
                os.remove(pid_file)
                return
            except OSError:
                os.remove(pid_file)
    else:
        process = subprocess.Popen(["feh", *feh_args, image_path])
        with open(pid_file, "w") as f:
            f.write(str(process.pid))


def main():
    parser = argparse.ArgumentParser(description="Toggle cheatsheet display.")
    parser.add_argument(
        "--cs", required=True, help="Cheatsheet name (e.g. hx, vim, elpris)"
    )
    args = parser.parse_args()

    cs = args.cs.lower()
    if cs not in CHEATSHEETS:
        print(
            f"Unknown cheatsheet: {cs}\nAvailable: {', '.join(CHEATSHEETS.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    toggle_image(CHEATSHEETS[cs])


if __name__ == "__main__":
    main()
