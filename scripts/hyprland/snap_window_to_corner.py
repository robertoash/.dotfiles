#!/usr/bin/env python3
import json
import subprocess
import sys


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


# Main logic
if __name__ == "__main__":
    window_info = get_active_window_info()

    if sys.argv[1] == "--lower-right":
        corner = ["d", "r"]
        move_window_to_corner(corner)
        sys.exit(0)

    if window_info:
        # Check if the window is floating
        if not window_info.get("floating"):
            sys.exit("Window is not floating. Exiting without snapping.")

        # Get window geometry and cursor position
        geometry = get_window_geometry(window_info)
        click_x, click_y = get_cursor_position()
        window_center_x = geometry["x"] + geometry["width"] // 2
        window_center_y = geometry["y"] + geometry["height"] // 2

        # Determine the boundary for corners (you can adjust this threshold)
        corner_threshold = 50  # Distance from corner to snap

        # Check if click is in the corner areas
        if (
            abs(click_x - geometry["x"]) < corner_threshold
            and abs(click_y - geometry["y"]) < corner_threshold
        ):
            corner = ["u", "l"]
        elif (
            abs(click_x - (geometry["x"] + geometry["width"])) < corner_threshold
            and abs(click_y - geometry["y"]) < corner_threshold
        ):
            corner = ["u", "r"]
        elif (
            abs(click_x - geometry["x"]) < corner_threshold
            and abs(click_y - (geometry["y"] + geometry["height"])) < corner_threshold
        ):
            corner = ["d", "l"]
        elif (
            abs(click_x - (geometry["x"] + geometry["width"])) < corner_threshold
            and abs(click_y - (geometry["y"] + geometry["height"])) < corner_threshold
        ):
            corner = ["d", "r"]
        else:
            sys.exit(0)

        # Snap to the determined corner
        move_window_to_corner(corner)
