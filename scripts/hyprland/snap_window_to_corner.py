#!/usr/bin/env python3
import json
import subprocess
import sys

CORNER_THRESHOLD = 50  # px


# Utility functions
def run_command(command):
    try:
        return subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT
        ).decode("utf-8")
    except subprocess.CalledProcessError as e:
        return e.output.decode()


def run_command_json(command):
    output = run_command(command)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return None


def get_cursor_position():
    output = run_command_json("hyprctl cursorpos -j")
    return output["x"], output["y"]


def get_active_window_info():
    return run_command_json("hyprctl activewindow -j") or {}


def get_clients():
    return run_command_json("hyprctl clients -j") or []


def get_window_by_address(address):
    return next((c for c in get_clients() if c["address"] == address), None)


def get_window_geometry(window_info):
    return {
        "x": window_info["at"][0],
        "y": window_info["at"][1],
        "width": window_info["size"][0],
        "height": window_info["size"][1],
    }


def move_window_to_corner(corner):
    for direction in corner:
        run_command(f"hyprctl dispatch movewindow {direction}")


def infer_corner():
    geometry = get_window_geometry(window_info)
    click_x, click_y = get_cursor_position()

    if (
        abs(click_x - geometry["x"]) < CORNER_THRESHOLD
        and abs(click_y - geometry["y"]) < CORNER_THRESHOLD
    ):
        corner = ["u", "l"]
    elif (
        abs(click_x - (geometry["x"] + geometry["width"])) < CORNER_THRESHOLD
        and abs(click_y - geometry["y"]) < CORNER_THRESHOLD
    ):
        corner = ["u", "r"]
    elif (
        abs(click_x - geometry["x"]) < CORNER_THRESHOLD
        and abs(click_y - (geometry["y"] + geometry["height"])) < CORNER_THRESHOLD
    ):
        corner = ["d", "l"]
    elif (
        abs(click_x - (geometry["x"] + geometry["width"])) < CORNER_THRESHOLD
        and abs(click_y - (geometry["y"] + geometry["height"])) < CORNER_THRESHOLD
    ):
        corner = ["d", "r"]
    else:
        sys.exit(0)

    return corner


# Main logic
if __name__ == "__main__":
    args = sys.argv[1:]
    forced_address = None
    corner = None

    for i, arg in enumerate(args):
        if arg == "--address" and i + 1 < len(args):
            forced_address = args[i + 1]
        elif arg in ("--lower-right", "--lower-left", "--upper-right", "--upper-left"):
            corner_map = {
                "--lower-left": ["d", "l"],
                "--upper-right": ["u", "r"],
                "--upper-left": ["u", "l"],
                "--lower-right": ["d", "r"],
            }
            corner = corner_map[arg]

    window_info = (
        get_window_by_address(forced_address)
        if forced_address
        else get_active_window_info()
    )
    if not window_info:
        sys.exit("❌ Could not find target window.")

    if not window_info.get("floating"):
        sys.exit("🚫 Window is not floating. Exiting.")

    # Corner via argument, or infer from cursor position
    if corner:
        move_window_to_corner(corner)
    else:
        corner = infer_corner()

        move_window_to_corner(corner)
