#!/usr/bin/env python3

from . import window_manager

CORNER_THRESHOLD = 50  # px


def get_cursor_position():
    """Get current cursor position."""
    cursor_info = window_manager.run_hyprctl(["cursorpos", "-j"])
    return cursor_info["x"], cursor_info["y"]


def get_window_geometry(window_info):
    """Extract window geometry from window info."""
    return {
        "x": window_info["at"][0],
        "y": window_info["at"][1],
        "width": window_info["size"][0],
        "height": window_info["size"][1],
    }


def move_window_to_corner(corner):
    """Move window to specified corner using hyprctl movewindow commands."""
    for direction in corner:
        window_manager.run_hyprctl_command(["dispatch", "movewindow", direction])


def infer_corner_from_cursor(window_info):
    """Infer which corner to snap to based on cursor position relative to window."""
    geometry = get_window_geometry(window_info)
    click_x, click_y = get_cursor_position()

    if (
        abs(click_x - geometry["x"]) < CORNER_THRESHOLD
        and abs(click_y - geometry["y"]) < CORNER_THRESHOLD
    ):
        return ["u", "l"]  # upper-left
    elif (
        abs(click_x - (geometry["x"] + geometry["width"])) < CORNER_THRESHOLD
        and abs(click_y - geometry["y"]) < CORNER_THRESHOLD
    ):
        return ["u", "r"]  # upper-right
    elif (
        abs(click_x - geometry["x"]) < CORNER_THRESHOLD
        and abs(click_y - (geometry["y"] + geometry["height"])) < CORNER_THRESHOLD
    ):
        return ["d", "l"]  # lower-left
    elif (
        abs(click_x - (geometry["x"] + geometry["width"])) < CORNER_THRESHOLD
        and abs(click_y - (geometry["y"] + geometry["height"])) < CORNER_THRESHOLD
    ):
        return ["d", "r"]  # lower-right
    else:
        return None  # Cursor not near any corner


def detect_current_corner(window_info):
    """Detect which corner the window is currently positioned in on its monitor."""
    geometry = get_window_geometry(window_info)

    # Get monitor info
    monitors = window_manager.run_hyprctl(["monitors", "-j"])
    current_monitor = None

    # Find which monitor the window is on
    for monitor in monitors:
        mon_x = monitor["x"]
        mon_y = monitor["y"]
        mon_width = monitor["width"]
        mon_height = monitor["height"]

        # Check if window center is within this monitor
        window_center_x = geometry["x"] + geometry["width"] // 2
        window_center_y = geometry["y"] + geometry["height"] // 2

        if (
            mon_x <= window_center_x < mon_x + mon_width
            and mon_y <= window_center_y < mon_y + mon_height
        ):
            current_monitor = monitor
            break

    if not current_monitor:
        return None

    # Calculate relative position within monitor
    mon_x = current_monitor["x"]
    mon_y = current_monitor["y"]
    mon_width = current_monitor["width"]
    mon_height = current_monitor["height"]

    # Check which corner window is closest to
    window_x = geometry["x"]
    window_y = geometry["y"]

    # Distance to each corner
    distances = {
        "upper-left": ((window_x - mon_x) ** 2 + (window_y - mon_y) ** 2) ** 0.5,
        "upper-right": ((window_x - (mon_x + mon_width)) ** 2 + (window_y - mon_y) ** 2)
        ** 0.5,
        "lower-left": ((window_x - mon_x) ** 2 + (window_y - (mon_y + mon_height)) ** 2)
        ** 0.5,
        "lower-right": (
            (window_x - (mon_x + mon_width)) ** 2
            + (window_y - (mon_y + mon_height)) ** 2
        )
        ** 0.5,
    }

    # Return the closest corner
    return min(distances, key=distances.get)


def mirror_corner(corner):
    """Mirror a corner position horizontally (left <-> right)."""
    mirror_map = {
        "upper-left": "upper-right",
        "upper-right": "upper-left",
        "lower-left": "lower-right",
        "lower-right": "lower-left",
    }
    return mirror_map.get(corner, corner)


def snap_window_to_corner(corner=None, window_address=None, relative_floating=False):
    """
    Snap a window to a specific corner or auto-detect based on cursor position.

    Args:
        corner: One of 'lower-left', 'lower-right', 'upper-left', 'upper-right',
                or None for auto-detect
        window_address: Specific window address, or None for smart targeting
        relative_floating: Use smart targeting to find floating windows

    Returns:
        0 on success, 1 on error
    """
    # Get target window
    original_active_address = None
    if window_address:
        # Explicit address provided - find and focus it
        clients = window_manager.get_clients()
        window_info = next((c for c in clients if c["address"] == window_address), None)
        if not window_info:
            print(f"❌ Could not find window with address {window_address}")
            return 1
        window_manager.focus_window(window_info["address"])
    else:
        # Use smart targeting or active window
        window_info, original_active_address = window_manager.get_target_window_with_focus(
            relative_floating
        )
        if not window_info:
            print("❌ Could not find window")
            return 1

    # Check if window is floating
    if not window_info.get("floating"):
        print("🚫 Window is not floating. Cannot snap to corner.")
        return 1

    # Determine corner
    if corner:
        corner_map = {
            "lower-left": ["d", "l"],
            "upper-right": ["u", "r"],
            "upper-left": ["u", "l"],
            "lower-right": ["d", "r"],
        }
        corner_directions = corner_map.get(corner)
        if not corner_directions:
            print(f"❌ Invalid corner: {corner}")
            return 1
    else:
        # Auto-detect corner from cursor position
        corner_directions = infer_corner_from_cursor(window_info)
        if not corner_directions:
            print("🚫 Cursor not near any corner. No action taken.")
            return 0

    # Move window to corner
    move_window_to_corner(corner_directions)

    # Get corner name for feedback
    corner_names = {
        ("u", "l"): "upper-left",
        ("u", "r"): "upper-right",
        ("d", "l"): "lower-left",
        ("d", "r"): "lower-right",
    }
    corner_name = corner_names.get(tuple(corner_directions), "unknown")
    print(f"✅ Window snapped to {corner_name} corner")

    # Restore focus to original window if we changed it
    if original_active_address:
        window_manager.focus_window(original_active_address)

    return 0
