#!/usr/bin/env python3

from . import monitor_utils, window_manager

CORNER_THRESHOLD = 50  # px


def get_cursor_position():
    """Get current cursor position."""
    cursor_info = window_manager.run_hyprctl(["cursorpos", "-j"])
    return cursor_info["x"], cursor_info["y"]


def move_window_to_corner(corner, window_address=None):
    """
    Move window to specified corner using hyprctl movewindow commands,
    then apply margin offset to account for gaps_out.

    Args:
        corner: List of directions like ["d", "r"] for lower-right
        window_address: Window address (hex string like "0x12345") or None for active window
    """
    for direction in corner:
        window_manager.run_hyprctl_command(["dispatch", "movewindow", direction])

    # Apply margin offset to account for gaps_out
    gaps_out = window_manager.get_hyprland_gaps_out()
    print(f"Debug: gaps_out = {gaps_out}, corner = {corner}")
    if gaps_out > 0:
        # Calculate offset based on corner position
        # corner is like ["d", "r"] or ["u", "l"]
        x_offset = -gaps_out if "r" in corner else gaps_out
        y_offset = -gaps_out if "d" in corner else gaps_out

        print(f"Debug: Applying offset x={x_offset}, y={y_offset} to window {window_address}")
        # Build command with window address - no space before address per Hyprland docs
        # Use -- to prevent negative numbers from being interpreted as flags
        if window_address:
            window_manager.run_hyprctl_command([
                "dispatch", "movewindowpixel",
                "--",
                f"{x_offset} {y_offset},address:{window_address}"
            ])
        else:
            # Fallback to active window (though this may not work)
            window_manager.run_hyprctl_command([
                "dispatch", "movewindowpixel",
                "--",
                f"{x_offset} {y_offset}"
            ])


def infer_corner_from_cursor(window_info):
    """Infer which corner to snap to based on cursor position relative to window."""
    geometry = monitor_utils.get_window_geometry(window_info)
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


def snap_window_to_corner(corner=None, window_address=None, relative_floating=False, sneaky=False):
    """
    Snap a window to a specific corner or auto-detect based on cursor position.

    Args:
        corner: One of 'lower-left', 'lower-right', 'upper-left', 'upper-right',
                or None for auto-detect
        window_address: Specific window address, or None for smart targeting
        relative_floating: Use smart targeting to find floating windows
        sneaky: Apply the 'sneaky' tag to the window

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
        target_address = window_address
    else:
        # Use smart targeting or active window
        window_info, original_active_address = window_manager.get_target_window_with_focus(
            relative_floating
        )
        if not window_info:
            print("❌ Could not find window")
            return 1
        target_address = window_info.get("address")

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
    move_window_to_corner(corner_directions, target_address)

    # Apply sneaky tag if requested
    if sneaky:
        window_manager.apply_sneaky_tag(target_address)

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
