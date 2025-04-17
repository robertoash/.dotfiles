#!/usr/bin/env python3
import json
import subprocess
import sys
from time import sleep

CORNER_THRESHOLD = 1  # px


def run(cmd):
    return subprocess.check_output(cmd, shell=True).decode()


def run_json(cmd):
    return json.loads(run(cmd))


def parse_direction(argv):
    if "--left" in argv:
        return "left"
    elif "--right" in argv:
        return "right"
    elif "--direction" in argv:
        try:
            idx = argv.index("--direction")
            direction = argv[idx + 1]
            if direction not in ("left", "right"):
                raise ValueError
            return direction
        except (IndexError, ValueError):
            print("❌ Usage: --direction [left|right]")
            sys.exit(1)
    else:
        print("❌ Must provide --left, --right, or --direction [left|right]")
        sys.exit(1)


def get_active_window_info():
    return run_json("hyprctl activewindow -j")


def get_monitor_layout():
    return run_json("hyprctl monitors -j")


def main():
    direction = parse_direction(sys.argv[1:])
    win_info = get_active_window_info()
    if not win_info.get("floating"):
        print("❌ Only works with floating windows.")
        sys.exit(1)

    window_width = win_info.get("size", [0, 0])[0]
    window_height = win_info.get("size", [0, 0])[1]
    monitor_index = win_info.get("monitor", None)
    was_pinned = win_info.get("pinned", False)

    monitors = get_monitor_layout()

    try:
        current_monitor = monitors[monitor_index]
    except IndexError:
        print(f"❌ Invalid monitor index: {monitor_index}")
        sys.exit(1)

    current_monitor_name = current_monitor["name"]

    # Sort monitors by their X coordinate
    sorted_monitors = sorted(monitors, key=lambda m: m["x"])

    current_index = next(
        (
            i
            for i, mon in enumerate(sorted_monitors)
            if mon["name"] == current_monitor_name
        ),
        None,
    )
    if current_index is None:
        print("❌ Could not find current monitor in sorted list.")
        sys.exit(1)

    if direction == "left":
        target_index = current_index - 1
    else:
        target_index = current_index + 1

    print("🧭 Sorted monitors:")
    for i, m in enumerate(sorted_monitors):
        print(f"  [{i}] {m['name']} x={m['x']} transform={m['transform']}")

    print(f"🖼️  Current monitor: {current_monitor_name} (sorted index: {current_index})")
    print(f"➡️  Direction: {direction} → Target index: {target_index}")

    if not (0 <= target_index < len(sorted_monitors)):
        print(f"❌ No monitor in direction: {direction}")
        sys.exit(1)

    target_monitor = sorted_monitors[target_index]

    # Correct for transform (rotation)
    transform = target_monitor["transform"]
    is_rotated = transform in (1, 3)

    mon_logical_width = (
        target_monitor["height"] if is_rotated else target_monitor["width"]
    )
    mon_logical_height = (
        target_monitor["width"] if is_rotated else target_monitor["height"]
    )

    # Final position: bottom-right corner of target monitor
    target_x = target_monitor["x"] + mon_logical_width - window_width - CORNER_THRESHOLD
    target_y = (
        target_monitor["y"] + mon_logical_height - window_height - CORNER_THRESHOLD
    )

    run(f"hyprctl dispatch moveactive exact {target_x} {target_y}")
    new_win_info = get_active_window_info()
    new_monitor_index = new_win_info.get("monitor", None)
    new_win_floating = new_win_info.get("floating", False)
    sleep(0.3)
    if new_monitor_index == monitor_index and new_win_floating:
        run("hyprctl dispatch settiled")
        run("hyprctl dispatch setfloating")
        run(f"hyprctl dispatch moveactive exact {target_x} {target_y}")
    new_win_info = get_active_window_info()
    is_pinned = new_win_info.get("pinned", False)
    print("🔄 Pinned:", was_pinned, "→", is_pinned)
    if was_pinned != is_pinned:
        run("hyprctl dispatch pin")


if __name__ == "__main__":
    main()
