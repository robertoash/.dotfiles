#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path
from datetime import datetime
import tempfile

SCREENSHOT_DIR = Path.home() / "images/screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now().strftime("%Y-%m-%d-%H%M%S")


def run(cmd, input_data=None):
    subprocess.run(cmd, shell=True, check=True, input=input_data)


def region_annotate():
    # Create a temp file for the initial screenshot
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_path = temp_file.name
    out_path = SCREENSHOT_DIR / f"annotated-{STAMP}.png"
    region = subprocess.check_output("slurp", shell=True).decode().strip()
    run(f'grim -g "{region}" "{temp_path}"')
    run(f'swappy -f "{temp_path}" -o "{out_path}"')
    # Optionally, delete temp file after use
    try:
        Path(temp_path).unlink()
    except Exception:
        pass


def region_direct_save():
    out_path = SCREENSHOT_DIR / f"region-{STAMP}.png"
    region = subprocess.check_output("slurp", shell=True).decode().strip()
    run(f'grim -g "{region}" -o "{out_path}"')


def clipboard():
    region = subprocess.check_output("slurp", shell=True).decode().strip()
    p1 = subprocess.Popen(f'grim -g "{region}" -', shell=True, stdout=subprocess.PIPE)
    subprocess.run("wl-copy", shell=True, stdin=p1.stdout)
    if p1.stdout:
        p1.stdout.close()
    p1.wait()


def window_direct_save():
    out_path = SCREENSHOT_DIR / f"window-{STAMP}.png"
    jq = r'''"\\(.at[0]),\\(.at[1]) \\(.size[0])x\\(.size[1])"'''
    geom = (
        subprocess.check_output(f"hyprctl activewindow -j | jq -j '{jq}'", shell=True)
        .decode()
        .strip()
    )
    run(f'grim -g "{geom}" -o "{out_path}"')


def window_annotate():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_path = temp_file.name
    out_path = SCREENSHOT_DIR / f"annotated-{STAMP}.png"
    jq = r'''"\\(.at[0]),\\(.at[1]) \\(.size[0])x\\(.size[1])"'''
    geom = (
        subprocess.check_output(f"hyprctl activewindow -j | jq -j '{jq}'", shell=True)
        .decode()
        .strip()
    )
    run(f'grim -g "{geom}" "{temp_path}"')
    run(f'swappy -f "{temp_path}" -o "{out_path}"')
    try:
        Path(temp_path).unlink()
    except Exception:
        pass


def monitor_annotate():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_path = temp_file.name
    out_path = SCREENSHOT_DIR / f"annotated-{STAMP}.png"
    monitor = (
        subprocess.check_output(
            "hyprctl monitors -j | jq -r '.[] | select(.focused) | .name'", shell=True
        )
        .decode()
        .strip()
    )
    run(f'grim -o "{monitor}" "{temp_path}"')
    run(f'swappy -f "{temp_path}" -o "{out_path}"')
    try:
        Path(temp_path).unlink()
    except Exception:
        pass


actions = {
    "region-annotate": region_annotate,
    "region-direct-save": region_direct_save,
    "clipboard": clipboard,
    "window-annotate": window_annotate,
    "window-direct-save": window_direct_save,
    "monitor-annotate": monitor_annotate,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        print(
            "Usage: take_screenshot.py [region-annotate|region-direct-save|clipboard|window-annotate|window-direct-save|monitor-annotate]"
        )
        sys.exit(1)
    actions[sys.argv[1]]()
