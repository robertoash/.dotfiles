#!/usr/bin/env python3

"""
Shared utilities for monitor-related calculations in hypr-window-ops.

This module provides consistent logic for:
- Monitor transform/rotation handling
- Reserved space (waybar, etc.) parsing
- Edge offset calculations (gaps + borders)
- Usable area boundaries
- Corner detection for snapped windows
"""

from . import window_manager


def get_monitor_with_transform(window_info):
    """
    Get the monitor that contains the window with corrected dimensions for transform/rotation.

    Args:
        window_info: Window info dict from hyprctl

    Returns:
        Monitor info dict with width/height swapped for portrait monitors (transform 1 or 3),
        or None if monitor not found
    """
    window_monitor_id = window_info.get("monitor")
    if window_monitor_id is None:
        return None

    monitors = window_manager.run_hyprctl(["monitors", "-j"])

    for monitor in monitors:
        if monitor.get("id") == window_monitor_id:
            # Account for transform/rotation
            # transform=1 or transform=3 means 90° or 270° rotation (portrait mode)
            # In these cases, width and height are swapped in actual screen space
            transform = monitor.get("transform", 0)
            if transform in [1, 3]:
                # Swap width and height for portrait monitors
                corrected_monitor = monitor.copy()
                corrected_monitor["width"], corrected_monitor["height"] = (
                    monitor["height"],
                    monitor["width"],
                )
                return corrected_monitor
            return monitor

    return None


def get_monitor_reserved_space(monitor):
    """
    Extract reserved space from monitor info.

    Reserved space is used by panels like waybar and is reported by Hyprland
    in the format [left, top, right, bottom].

    Args:
        monitor: Monitor info dict from hyprctl

    Returns:
        Dict with 'top', 'bottom', 'left', 'right' keys (in pixels)
    """
    reserved = monitor.get("reserved", [0, 0, 0, 0])
    return {
        "left": reserved[0],
        "top": reserved[1],
        "right": reserved[2],
        "bottom": reserved[3],
    }


def get_edge_offset():
    """
    Calculate the edge offset for floating windows to align with tiled windows.

    Floating windows should align with tiled windows which respect both gaps_out
    and borders. The edge offset is: gaps_out + (border_size * 2)

    Returns:
        int: Edge offset in pixels
    """
    gaps_out = window_manager.get_hyprland_gaps_out()
    border_size = window_manager.get_hyprland_border_size()
    return gaps_out + border_size * 2


def get_monitor_usable_area(monitor):
    """
    Calculate the usable area boundaries for a monitor.

    This accounts for:
    - Monitor position and dimensions
    - Reserved space (waybar, panels, etc.)
    - Edge offset (gaps + borders)

    Args:
        monitor: Monitor info dict from hyprctl (should be transform-corrected)

    Returns:
        Dict with 'min_x', 'min_y', 'max_x', 'max_y' boundaries in absolute coordinates
    """
    reserved = get_monitor_reserved_space(monitor)
    edge_offset = get_edge_offset()

    mon_x = monitor["x"]
    mon_y = monitor["y"]
    mon_width = monitor["width"]
    mon_height = monitor["height"]

    return {
        "min_x": mon_x + edge_offset,
        "min_y": mon_y + reserved["top"] + edge_offset,
        "max_x": mon_x + mon_width - edge_offset,
        "max_y": mon_y + mon_height - reserved["bottom"] - edge_offset,
    }


def get_window_geometry(window_info):
    """
    Extract window geometry from window info.

    Args:
        window_info: Window info dict from hyprctl

    Returns:
        Dict with 'x', 'y', 'width', 'height' keys
    """
    return {
        "x": window_info["at"][0],
        "y": window_info["at"][1],
        "width": window_info["size"][0],
        "height": window_info["size"][1],
    }


def detect_window_corner(window_info, snap_threshold=10):
    """
    Detect which corner the window is currently positioned in on its monitor.

    This checks if the window's position matches expected snap positions for each corner,
    accounting for gaps, borders, and reserved space.

    Args:
        window_info: Window info dict from hyprctl
        snap_threshold: Pixels tolerance for considering window "snapped" (default: 10)

    Returns:
        Corner name ('upper-left', 'upper-right', 'lower-left', 'lower-right') if window
        is snapped to a corner, otherwise None
    """
    geometry = get_window_geometry(window_info)
    monitor = get_monitor_with_transform(window_info)

    if not monitor:
        return None

    # Get usable area and gaps
    reserved = get_monitor_reserved_space(monitor)
    gaps_out = window_manager.get_hyprland_gaps_out()

    mon_x = monitor["x"]
    mon_y = monitor["y"]
    mon_width = monitor["width"]
    mon_height = monitor["height"]

    window_x = geometry["x"]
    window_y = geometry["y"]

    # Calculate expected snap positions (matching what movewindow + gaps_out produces)
    # Hyprland's movewindow accounts for reserved space automatically
    expected_positions = {
        "upper-left": {
            "x": mon_x + gaps_out,
            "y": mon_y + reserved["top"] + gaps_out,
        },
        "upper-right": {
            "x": mon_x + mon_width - geometry["width"] - gaps_out,
            "y": mon_y + reserved["top"] + gaps_out,
        },
        "lower-left": {
            "x": mon_x + gaps_out,
            "y": mon_y + mon_height - geometry["height"] - reserved["bottom"] - gaps_out,
        },
        "lower-right": {
            "x": mon_x + mon_width - geometry["width"] - gaps_out,
            "y": mon_y + mon_height - geometry["height"] - reserved["bottom"] - gaps_out,
        },
    }

    # Check each corner for snap alignment
    for corner, expected in expected_positions.items():
        if (
            abs(window_x - expected["x"]) < snap_threshold
            and abs(window_y - expected["y"]) < snap_threshold
        ):
            return corner

    return None


def mirror_corner(corner):
    """
    Mirror a corner position horizontally (left <-> right).

    Args:
        corner: Corner name string

    Returns:
        Mirrored corner name
    """
    mirror_map = {
        "upper-left": "upper-right",
        "upper-right": "upper-left",
        "lower-left": "lower-right",
        "lower-right": "lower-left",
    }
    return mirror_map.get(corner, corner)
