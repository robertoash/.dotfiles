#!/usr/bin/env python3
import json
import subprocess
import sys


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


if __name__ == "__main__":
    skip_cursor = "--lower-right" in sys.argv
    window_info = get_active_window_info()

    if window_info:
        was_pinned = "pinned" in window_info and window_info["pinned"]
        if was_pinned:
            run_command("hyprctl dispatch pin")

        if skip_cursor:
            corner = ["d", "r"]  # Snap to lower right corner
        else:
            click_x, click_y = get_cursor_position()
            geometry = get_window_geometry(window_info)
            window_center_x = geometry["x"] + geometry["width"] // 2
            window_center_y = geometry["y"] + geometry["height"] // 2

            # Determine closest corner of the window based on the click position
            if click_x < window_center_x and click_y < window_center_y:
                corner = ["u", "l"]
            elif click_x >= window_center_x and click_y < window_center_y:
                corner = ["u", "r"]
            elif click_x < window_center_x and click_y >= window_center_y:
                corner = ["d", "l"]
            else:
                corner = ["d", "r"]

        move_window_to_corner(corner)

        if was_pinned:
            run_command("hyprctl dispatch pin")
