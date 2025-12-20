#!/usr/bin/env python3

from time import sleep

from . import window_manager


def detect_current_corner(window_info, monitors):
    """Detect which corner the window is currently positioned in on its monitor."""
    geometry = {
        "x": window_info["at"][0],
        "y": window_info["at"][1],
        "width": window_info["size"][0],
        "height": window_info["size"][1],
    }

    # Find current monitor
    monitor_index = window_info.get("monitor", None)
    current_monitor = monitors[monitor_index]

    # Handle monitor rotation for coordinate space
    transform = current_monitor["transform"]
    is_rotated = transform in (1, 3)  # 90° or 270° rotation

    # Convert physical dimensions to logical coordinate space
    mon_x = current_monitor["x"]
    mon_y = current_monitor["y"]
    mon_logical_width = (
        current_monitor["height"] if is_rotated else current_monitor["width"]
    )
    mon_logical_height = (
        current_monitor["width"] if is_rotated else current_monitor["height"]
    )

    # Use window center for quadrant detection
    window_center_x = geometry["x"] + geometry["width"] // 2
    window_center_y = geometry["y"] + geometry["height"] // 2

    # Determine quadrant based on window center
    mid_x = mon_x + mon_logical_width // 2
    mid_y = mon_y + mon_logical_height // 2

    if window_center_x < mid_x and window_center_y < mid_y:
        corner = "upper-left"
    elif window_center_x >= mid_x and window_center_y < mid_y:
        corner = "upper-right"
    elif window_center_x < mid_x and window_center_y >= mid_y:
        corner = "lower-left"
    else:
        corner = "lower-right"

    return corner


def mirror_corner(corner):
    """Mirror a corner position horizontally (left <-> right)."""
    mirror_map = {
        "upper-left": "upper-right",
        "upper-right": "upper-left",
        "lower-left": "lower-right",
        "lower-right": "lower-left",
    }
    return mirror_map.get(corner, corner)


def move_window_to_corner(corner, window_address=None):
    """
    Move window to specified corner using hyprctl movewindow commands,
    then apply margin offset to account for gaps_out.

    Args:
        corner: Corner name like "lower-right", "upper-left", etc.
        window_address: Window address (hex string like "0x12345") or None for active window
    """
    corner_map = {
        "lower-left": ["d", "l"],
        "upper-right": ["u", "r"],
        "upper-left": ["u", "l"],
        "lower-right": ["d", "r"],
    }
    corner_directions = corner_map.get(corner, ["d", "r"])

    for direction in corner_directions:
        window_manager.run_hyprctl_command(["dispatch", "movewindow", direction])

    # Apply margin offset to account for gaps_out
    gaps_out = window_manager.get_hyprland_gaps_out()
    if gaps_out > 0:
        # Calculate offset based on corner position
        x_offset = -gaps_out if "r" in corner_directions else gaps_out
        y_offset = -gaps_out if "d" in corner_directions else gaps_out

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


def move_window_to_monitor(direction, debug=False, relative_floating=False):
    """
    Move window to adjacent monitor with corner mirroring.

    Args:
        direction: "left" or "right"
        debug: Whether to print debug information
        relative_floating: Use smart targeting to find floating windows

    Returns:
        0 on success, 1 on error
    """
    win_info, original_active_address = window_manager.get_target_window_with_focus(
        relative_floating
    )

    if not win_info.get("floating"):
        print("❌ Only works with floating windows.")
        return 1

    monitor_index = win_info.get("monitor", None)
    was_pinned = win_info.get("pinned", False)

    # Get monitor layout
    monitors = window_manager.run_hyprctl(["monitors", "-j"])

    try:
        current_monitor = monitors[monitor_index]
    except IndexError:
        print(f"❌ Invalid monitor index: {monitor_index}")
        return 1

    current_monitor_name = current_monitor["name"]

    # Detect current corner position
    current_corner = detect_current_corner(win_info, monitors)
    if debug:
        print(f"🔍 Current corner: {current_corner}")

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
        return 1

    if direction == "left":
        target_index = current_index - 1
    else:
        target_index = current_index + 1

    if debug:
        print("🧭 Sorted monitors:")
        for i, m in enumerate(sorted_monitors):
            print(f"  [{i}] {m['name']} x={m['x']} transform={m['transform']}")

        print(
            f"🖼️  Current monitor: {current_monitor_name} (sorted index: {current_index})"
        )
        print(f"➡️  Direction: {direction} → Target index: {target_index}")

    if not (0 <= target_index < len(sorted_monitors)):
        print(f"❌ No monitor in direction: {direction}")
        return 1

    # Mirror the corner position (left <-> right)
    target_corner = mirror_corner(current_corner)
    if debug:
        print(f"🪞 Mirrored corner: {current_corner} → {target_corner}")

    # Unpin window if it's pinned (pinned windows don't move between monitors)
    if was_pinned:
        if debug:
            print("📌 Temporarily unpinning window for monitor move")
        window_manager.run_hyprctl_command(["dispatch", "pin"])

    # Move to target monitor using proper syntax
    target_monitor_name = sorted_monitors[target_index]["name"]
    if debug:
        print(f"🎯 Moving to monitor: {target_monitor_name}")
    window_manager.run_hyprctl_command(
        ["dispatch", "movewindow", f"mon:{target_monitor_name}"]
    )

    # Brief delay to ensure monitor change completes
    sleep(0.2)

    # Now move to the mirrored corner using the same method as snap_windows.py
    window_address = win_info.get("address")
    move_window_to_corner(target_corner, window_address)

    # Re-pin window if it was originally pinned
    if was_pinned:
        if debug:
            print("📌 Re-pinning window")
        window_manager.run_hyprctl_command(["dispatch", "pin"])

    # Verify final state
    if debug:
        new_win_info = window_manager.run_hyprctl(["activewindow", "-j"])
        new_monitor_index = new_win_info.get("monitor", None)
        is_pinned = new_win_info.get("pinned", False)
        print(f"✅ Moved from monitor {monitor_index} to {new_monitor_index}")
        print("🔄 Pinned:", was_pinned, "→", is_pinned)

    # Restore focus to original window if we changed it
    if original_active_address:
        window_manager.focus_window(original_active_address)

    return 0
