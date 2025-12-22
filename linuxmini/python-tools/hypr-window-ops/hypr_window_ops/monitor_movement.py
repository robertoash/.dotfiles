#!/usr/bin/env python3

import subprocess
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


def get_corner_directions(corner):
    """Get movement directions for a corner name."""
    corner_map = {
        "lower-left": ["d", "l"],
        "upper-right": ["u", "r"],
        "upper-left": ["u", "l"],
        "lower-right": ["d", "r"],
    }
    return corner_map.get(corner, ["d", "r"])


def build_monitor_corner_batch(window_address, target_monitor_name, corner, was_pinned=False):
    """
    Build a batch command to move a window to a monitor and snap to corner (without gaps yet).

    Args:
        window_address: The window address
        target_monitor_name: Target monitor name
        corner: Corner name ('upper-left', etc.)
        was_pinned: Whether window is pinned (will be temporarily unpinned)

    Returns:
        Tuple of (batch_cmd_string, corner_directions) - gaps applied separately after
    """
    batch_commands = []

    # Unpin if needed
    if was_pinned:
        batch_commands.append(f"dispatch pin address:{window_address}")

    # Focus, move, snap to corner
    batch_commands.append(f"dispatch focuswindow address:{window_address}")
    batch_commands.append(f"dispatch movewindow mon:{target_monitor_name}")

    corner_directions = get_corner_directions(corner)
    for direction in corner_directions:
        batch_commands.append(f"dispatch movewindow {direction}")

    # Re-pin if needed
    if was_pinned:
        batch_commands.append(f"dispatch pin address:{window_address}")

    return " ; ".join(batch_commands), corner_directions


def apply_corner_gaps_offset(window_address, corner_directions):
    """
    Apply gaps offset after batch command (movewindowpixel with address doesn't work in batch).

    Args:
        window_address: The window address
        corner_directions: List of corner directions like ["d", "r"]
    """
    gaps_out = window_manager.get_hyprland_gaps_out()
    if gaps_out > 0:
        sleep(0.05)
        x_offset = -gaps_out if "r" in corner_directions else gaps_out
        y_offset = -gaps_out if "d" in corner_directions else gaps_out
        window_manager.run_hyprctl_command([
            "dispatch", "movewindowpixel", "--", f"{x_offset} {y_offset},address:{window_address}"
        ])
        sleep(0.02)


def move_window_to_corner(corner, window_address=None):
    """
    Move window to specified corner using hyprctl movewindow commands,
    then apply margin offset to account for gaps_out.

    Args:
        corner: Corner name like "lower-right", "upper-left", etc.
        window_address: Window address (hex string like "0x12345") or None for active window
    """
    corner_directions = get_corner_directions(corner)

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


def move_window_to_monitor_and_corner(
    window_address,
    target_monitor_name,
    corner,
    was_pinned=False,
    restore_focus_to=None
):
    """
    Move a window to a specific monitor and corner.

    Args:
        window_address: The window address
        target_monitor_name: Target monitor name
        corner: Corner name ('upper-left', etc.)
        was_pinned: Whether window is pinned
        restore_focus_to: Optional address to restore focus to after move

    Returns:
        0 on success, 1 on error
    """
    # Build and execute batch command
    batch_cmd, corner_directions = build_monitor_corner_batch(
        window_address, target_monitor_name, corner, was_pinned
    )
    subprocess.run(["hyprctl", "--batch", batch_cmd], capture_output=True, text=True)

    # Apply gaps offset after batch
    apply_corner_gaps_offset(window_address, corner_directions)

    # Restore focus if requested
    if restore_focus_to and restore_focus_to != window_address:
        sleep(0.05)
        window_manager.focus_window(restore_focus_to)
        sleep(0.02)

    return 0


def move_window_to_monitor(direction, debug=False, relative_floating=False, sneaky=False):
    """
    Move window to adjacent monitor with corner mirroring.

    Args:
        direction: "left" or "right"
        debug: Whether to print debug information
        relative_floating: Use smart targeting to find floating windows
        sneaky: Apply the 'sneaky' tag to the window

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

    # Use batch command for atomic move: unpin → focus → move monitor → snap corner → repin
    window_address = win_info.get("address")
    target_monitor_name = sorted_monitors[target_index]["name"]

    if debug:
        print(f"🎯 Moving to monitor: {target_monitor_name}, corner: {target_corner}")

    # Build and execute batch command (without gaps yet)
    batch_cmd, corner_directions = build_monitor_corner_batch(window_address, target_monitor_name, target_corner, was_pinned)
    subprocess.run(["hyprctl", "--batch", batch_cmd], capture_output=True, text=True)

    # Apply gaps offset after batch
    apply_corner_gaps_offset(window_address, corner_directions)

    # Restore focus to original window if we changed it (outside batch to ensure completion)
    if original_active_address and original_active_address != window_address:
        sleep(0.05)
        window_manager.focus_window(original_active_address)
        sleep(0.02)

    # Apply sneaky tag if requested
    if sneaky:
        window_manager.apply_sneaky_tag(window_address)

    # Verify final state
    if debug:
        new_win_info = window_manager.run_hyprctl(["activewindow", "-j"])
        new_monitor_index = new_win_info.get("monitor", None)
        is_pinned = new_win_info.get("pinned", False)
        print(f"✅ Moved from monitor {monitor_index} to {new_monitor_index}")
        print("🔄 Pinned:", was_pinned, "→", is_pinned)

    return 0
