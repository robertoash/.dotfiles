#!/usr/bin/env python3

import json
import subprocess


def get_monitors():
    result = subprocess.run(["hyprctl", "-j", "monitors"], stdout=subprocess.PIPE)
    monitors = json.loads(result.stdout)
    return monitors


def focus_next_monitor():
    monitors = get_monitors()
    focused_index = next((i for i, m in enumerate(monitors) if m.get("focused")), None)
    if focused_index is not None:
        next_index = (focused_index + 1) % len(monitors)
        next_monitor = monitors[next_index]["name"]
        subprocess.run(["hyprctl", "dispatch", "focusmonitor", next_monitor])


if __name__ == "__main__":
    focus_next_monitor()
