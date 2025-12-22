#!/usr/bin/env python3
"""
Sneaky Window Monitor - Keeps sneaky-tagged windows away from the active window.

This script continuously monitors windows tagged with 'sneaky' and ensures they
don't overlap with the currently active window. When overlap is detected, it
moves the sneaky window to a different corner or monitor.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the hypr-window-ops module to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "python-tools" / "hypr-window-ops"))

try:
    from hypr_window_ops import snap_windows, window_manager, monitor_movement
except ImportError:
    print("Error: Could not import hypr-window-ops modules. Make sure the package is installed.", file=sys.stderr)
    sys.exit(1)


def run_hyprctl(command: List[str]) -> Optional[Dict]:
    """Run a hyprctl command and return the parsed JSON output."""
    try:
        result = subprocess.run(
            ["hyprctl"] + command,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Error running hyprctl {' '.join(command)}: {e}", file=sys.stderr)
        return None


def run_hyprctl_dispatch(command: List[str]) -> bool:
    """Run a hyprctl dispatch command."""
    try:
        result = subprocess.run(
            ["hyprctl", "dispatch"] + command,
            capture_output=True,
            text=True,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def get_sneaky_windows() -> List[Dict]:
    """Get all windows with the 'sneaky' tag."""
    return window_manager.get_sneaky_windows()


def get_active_window() -> Optional[Dict]:
    """Get the currently active window."""
    return run_hyprctl(["activewindow", "-j"])


def get_monitors() -> List[Dict]:
    """Get all monitors."""
    return run_hyprctl(["monitors", "-j"]) or []


def rectangles_overlap(rect1: Tuple[int, int, int, int], rect2: Tuple[int, int, int, int]) -> bool:
    """
    Check if two rectangles overlap.

    Args:
        rect1: (x, y, width, height) of first rectangle
        rect2: (x, y, width, height) of second rectangle

    Returns:
        True if rectangles overlap, False otherwise
    """
    x1, y1, w1, h1 = rect1
    x2, y2, w2, h2 = rect2

    # Check if one rectangle is to the left of the other
    if x1 + w1 <= x2 or x2 + w2 <= x1:
        return False

    # Check if one rectangle is above the other
    if y1 + h1 <= y2 or y2 + h2 <= y1:
        return False

    return True


def calculate_corner_position(monitor: Dict, corner: str, window_size: Tuple[int, int]) -> Tuple[int, int]:
    """
    Calculate the position for a window at a given corner of a monitor.

    Args:
        monitor: Monitor information dict from hyprctl
        corner: One of 'upper-left', 'upper-right', 'lower-left', 'lower-right'
        window_size: (width, height) of the window

    Returns:
        (x, y) position for the window
    """
    monitor_x = monitor["x"]
    monitor_y = monitor["y"]

    # Handle monitor rotation for coordinate space (same logic as monitor_movement.py)
    transform = monitor["transform"]
    is_rotated = transform in (1, 3)  # 90° or 270° rotation

    # Convert physical dimensions to logical coordinate space
    monitor_width = monitor["height"] if is_rotated else monitor["width"]
    monitor_height = monitor["width"] if is_rotated else monitor["height"]

    window_width, window_height = window_size

    # Get the actual gap value from Hyprland (must match snap_windows.py)
    gap = window_manager.get_hyprland_gaps_out()

    if corner == "upper-left":
        return (monitor_x + gap, monitor_y + gap)
    elif corner == "upper-right":
        return (monitor_x + monitor_width - window_width - gap, monitor_y + gap)
    elif corner == "lower-left":
        return (monitor_x + gap, monitor_y + monitor_height - window_height - gap)
    elif corner == "lower-right":
        return (monitor_x + monitor_width - window_width - gap, monitor_y + monitor_height - window_height - gap)

    return (monitor_x, monitor_y)


def find_non_overlapping_corner(
    sneaky_window: Dict,
    active_window: Dict,
    current_monitor: Dict
) -> Optional[str]:
    """
    Find a corner on the current monitor where the sneaky window won't overlap with the active window.

    Args:
        sneaky_window: The sneaky window dict
        active_window: The active window dict
        current_monitor: The current monitor dict

    Returns:
        Corner name ('upper-left', etc.) or None if all corners overlap
    """
    sneaky_size = (sneaky_window["size"][0], sneaky_window["size"][1])
    active_rect = (
        active_window["at"][0],
        active_window["at"][1],
        active_window["size"][0],
        active_window["size"][1]
    )

    # Check all four corners regardless of monitor orientation (bottom corners first)
    corners = ["lower-left", "lower-right", "upper-left", "upper-right"]

    for corner in corners:
        # Calculate where the sneaky window would be at this corner
        pos_x, pos_y = calculate_corner_position(current_monitor, corner, sneaky_size)
        sneaky_rect = (pos_x, pos_y, sneaky_size[0], sneaky_size[1])

        # Check if this position overlaps with the active window
        if not rectangles_overlap(sneaky_rect, active_rect):
            return corner

    return None


def move_window_to_corner(window_address: str, corner: str) -> bool:
    """
    Move a window to a specific corner using the snap_windows module.

    Args:
        window_address: The window address
        corner: Corner name ('upper-left', 'upper-right', 'lower-left', 'lower-right')

    Returns:
        True if successful, False otherwise
    """
    # Use the existing snap_windows functionality
    result = snap_windows.snap_window_to_corner(
        corner=corner,
        window_address=window_address,
        relative_floating=False
    )
    return result == 0


def detect_bounce_pattern(
    jump_history: List[Tuple[str, int, str, float]],
    proposed_corner: str,
    proposed_monitor_id: int,
    active_window_address: str,
    time_window: float = 10.0,
    debug: bool = False
) -> bool:
    """
    Detect if moving to avoid this window would create a bouncing pattern.

    A bounce pattern is detected when we're repeatedly jumping to avoid the same 2 windows.
    This is window-aware - it tracks which window caused each jump, not just the corner.

    Args:
        jump_history: List of (corner, monitor_id, active_window_address, timestamp) tuples
        proposed_corner: The corner we're considering moving to
        proposed_monitor_id: The monitor ID we're considering
        active_window_address: The window we're trying to avoid now
        time_window: Time window in seconds to consider for bounce detection
        debug: Enable debug output

    Returns:
        True if this move would create a bounce pattern, False otherwise
    """
    if len(jump_history) < 3:
        if debug:
            print(f"  [Bounce Check] Not enough history ({len(jump_history)} < 3)")
        return False

    # Use the last 10 entries instead of time-based filtering for more predictable behavior
    recent_jumps = jump_history[-10:]

    # Filter jumps to only those on the proposed monitor
    # Since we now track "window at target location", we just filter by monitor ID
    monitor_jumps = [
        (corner, mon_id, win_addr, ts)
        for corner, mon_id, win_addr, ts in recent_jumps
        if mon_id == proposed_monitor_id
    ]

    if debug:
        print(f"  [Bounce Check] Total recent jumps: {len(recent_jumps)}, on monitor {proposed_monitor_id}: {len(monitor_jumps)}")

    # Need at least 2 jumps on this monitor to detect a pattern
    if len(monitor_jumps) < 2:
        if debug:
            print(f"  [Bounce Check] Not enough jumps on monitor {proposed_monitor_id}")
        return False

    # Extract positions and window addresses for this monitor only
    window_sequence = [win_addr for _, _, win_addr, _ in monitor_jumps]
    position_sequence = [(corner, mon_id) for corner, mon_id, _, _ in monitor_jumps]

    proposed_position = (proposed_corner, proposed_monitor_id)

    if debug:
        print(f"  [Bounce Check] Window sequence on monitor {proposed_monitor_id}: {[addr[-8:] for addr in window_sequence]}")
        print(f"  [Bounce Check] Positions: {position_sequence}")
        print(f"  [Bounce Check] Proposed position: {proposed_position}")
        print(f"  [Bounce Check] Current active window: {active_window_address[-8:]}")

    # Check if we're alternating between the same 2 windows on this monitor
    unique_windows = list(set(window_sequence))
    unique_positions = list(set(position_sequence))

    if len(unique_windows) == 2 and active_window_address in unique_windows:
        # Check if we have an A→B→A→B pattern with these windows
        # Count occurrences
        count_current = window_sequence.count(active_window_address)
        other_window = [w for w in unique_windows if w != active_window_address][0]
        count_other = window_sequence.count(other_window)

        if debug:
            print(f"  [Bounce Check] Two windows detected: counts {count_current} vs {count_other}")
            print(f"  [Bounce Check] Unique positions in history: {len(unique_positions)}")

        # Once we have enough history ON THIS MONITOR, be more aggressive
        if len(monitor_jumps) >= 3:
            # We have history on this monitor - detect bounce on 2nd repetition (A→B pattern)
            last_2_windows = window_sequence[-2:]
            if debug:
                print(f"  [Bounce Check] Last 2 windows on this monitor: {[addr[-8:] for addr in last_2_windows]}")

            # If last 2 are the two alternating windows
            if len(last_2_windows) == 2 and last_2_windows[0] != last_2_windows[1]:
                # Check if we're about to repeat either of them
                if active_window_address in last_2_windows:
                    # Pattern [A, B] and about to avoid A or B again
                    # Only bounce if the proposed position is one we've already used
                    if proposed_position in position_sequence:
                        if debug:
                            print(f"  [Bounce Check] ⚠️  BOUNCE DETECTED! (A→B pattern, position {proposed_position} in history)")
                        return True
                    else:
                        if debug:
                            print(f"  [Bounce Check] ✓ New position {proposed_position} - NOT a bounce")
                        return False

        # Fallback for initial detection (need 3 jumps on this monitor to establish pattern)
        if abs(count_current - count_other) <= 1 and len(monitor_jumps) >= 3:
            # Verify it's actually alternating, not just two windows appearing randomly
            last_3_windows = window_sequence[-3:]
            if debug:
                print(f"  [Bounce Check] Last 3 windows: {[addr[-8:] for addr in last_3_windows]}")

            # Pattern like [A, B, A] and now avoiding B again - that's a 4th jump in alternating pattern
            # Check if last 3 form an alternating pattern
            if last_3_windows[0] == last_3_windows[2] and last_3_windows[1] != last_3_windows[0]:
                # This is an alternating pattern [A, B, A] or [B, A, B]
                # If we're about to avoid the "other" window (the one that appears once), that's potentially a bounce
                if active_window_address != last_3_windows[0]:
                    # BUT: only bounce if the proposed position is one we've ALREADY been bouncing between
                    # Moving to a NEW position (like a different monitor) should NOT be considered a bounce
                    if proposed_position in position_sequence:
                        if debug:
                            print(f"  [Bounce Check] ⚠️  BOUNCE DETECTED! (A→B→A pattern, position {proposed_position} in sequence)")
                        return True
                    else:
                        if debug:
                            print(f"  [Bounce Check] ✓ New position {proposed_position} - NOT a bounce")
                        return False

    if debug:
        print(f"  [Bounce Check] No bounce pattern detected")
    return False


def get_bounce_windows(
    jump_history: List[Tuple[str, int, str, float]],
    monitor_id: Optional[int] = None,
    time_window: float = 10.0  # Parameter kept for compatibility but not used
) -> List[str]:
    """
    Get the list of windows involved in recent bounce pattern on a specific monitor.

    Args:
        jump_history: Jump history for this window
        monitor_id: Optional monitor ID to filter by (if None, checks all monitors)
        time_window: (Deprecated) Not used - we check last 10 entries instead

    Returns:
        List of window addresses involved in recent bouncing
    """
    if len(jump_history) < 3:
        return []

    # Use last 10 entries instead of time-based filtering
    recent_jumps = jump_history[-10:]

    # Filter by monitor if specified
    if monitor_id is not None:
        recent_jumps = [
            (corner, mon_id, win_addr, ts)
            for corner, mon_id, win_addr, ts in recent_jumps
            if mon_id == monitor_id
        ]

    if len(recent_jumps) < 2:
        return []

    window_sequence = [win_addr for _, _, win_addr, _ in recent_jumps]
    unique_windows = list(set(window_sequence))

    # If alternating between 2 windows, return both
    if len(unique_windows) == 2:
        counts = {w: window_sequence.count(w) for w in unique_windows}
        if abs(counts[unique_windows[0]] - counts[unique_windows[1]]) <= 1:
            return unique_windows

    return []


def find_alternative_corner(
    sneaky_window: Dict,
    active_window: Dict,
    current_monitor: Dict,
    monitors: List[Dict],
    all_windows: List[Dict],
    jump_history: List[Tuple[str, int, str, float]],
    cooldown_positions: Dict[Tuple[str, int], float],
    excluded_corner: str,
    debug: bool = False
) -> Optional[Tuple[str, int]]:
    """
    Find an alternative corner that won't bounce and won't overlap with bounce windows.

    Args:
        sneaky_window: The sneaky window dict
        active_window: The active window dict
        current_monitor: The current monitor dict
        monitors: List of all monitors
        all_windows: List of all windows to check overlap against
        jump_history: Jump history for this window
        cooldown_positions: Dict mapping (corner, monitor_id) to expiry timestamp
        excluded_corner: The corner to exclude (the one that would cause bouncing)

    Returns:
        Tuple of (corner, monitor_id) or None if no alternative found
    """
    sneaky_size = (sneaky_window["size"][0], sneaky_window["size"][1])
    current_monitor_id = current_monitor["id"]
    current_time = time.time()

    # Get windows involved in bounce pattern on current monitor - avoid overlapping with ANY of them
    bounce_windows = get_bounce_windows(jump_history, monitor_id=current_monitor_id)
    sneaky_address = sneaky_window.get("address")
    windows_to_avoid = [active_window]

    if bounce_windows:
        if debug:
            print(f"  [Alternative] Bounce windows on monitor {current_monitor_id}: {[addr[-8:] for addr in bounce_windows]}")
        # Add all bounce windows to avoid list, EXCEPT the sneaky window itself
        for window in all_windows:
            addr = window.get("address")
            if addr in bounce_windows and addr != sneaky_address:
                windows_to_avoid.append(window)

    if debug:
        print(f"  [Alternative] Avoiding {len(windows_to_avoid)} windows (excluding sneaky window)")

    corners = ["lower-left", "lower-right", "upper-left", "upper-right"]

    if debug:
        print(f"  [Alternative] Trying current monitor {current_monitor_id}...")

    # Try all corners on current monitor
    for corner in corners:
        if corner == excluded_corner:
            if debug:
                print(f"    - {corner}: ✗ excluded (would bounce)")
            continue

        position = (corner, current_monitor_id)

        # Check cooldown - skip if this position is still in cooldown
        if position in cooldown_positions and cooldown_positions[position] > current_time:
            if debug:
                print(f"    - {corner}: ✗ cooldown")
            continue

        # Check if this would create a bounce pattern
        if detect_bounce_pattern(jump_history, corner, current_monitor_id, active_window.get("address", ""), debug=False):
            if debug:
                print(f"    - {corner}: ✗ would bounce")
            continue

        # Calculate position and check for overlap with all windows we need to avoid
        pos_x, pos_y = calculate_corner_position(current_monitor, corner, sneaky_size)
        sneaky_rect = (pos_x, pos_y, sneaky_size[0], sneaky_size[1])

        # Check overlap with all windows to avoid
        overlaps = False
        for window in windows_to_avoid:
            window_rect = (
                window["at"][0],
                window["at"][1],
                window["size"][0],
                window["size"][1]
            )
            if rectangles_overlap(sneaky_rect, window_rect):
                overlaps = True
                if debug:
                    print(f"    - {corner}: ✗ overlaps with {window.get('address', '')[-8:]}")
                break

        if not overlaps:
            if debug:
                print(f"  [Alternative] ✓ Found on same monitor: {corner}")
            return (corner, current_monitor_id)

    if debug:
        print(f"  [Alternative] No safe corner on current monitor, trying other monitors...")
        print(f"  [Alternative] Total monitors: {len(monitors)}, current: {current_monitor_id}")

    # No safe corner on current monitor, try other monitors
    for monitor in monitors:
        if monitor["id"] == current_monitor_id:
            continue

        monitor_id = monitor["id"]

        if debug:
            print(f"  [Alternative] Trying monitor {monitor_id} ({monitor.get('name', 'unknown')})")

        for corner in corners:
            position = (corner, monitor_id)

            # Check cooldown
            if position in cooldown_positions and cooldown_positions[position] > current_time:
                if debug:
                    print(f"    - {corner}: ✗ cooldown")
                continue

            # Check if this would create a bounce pattern
            if detect_bounce_pattern(jump_history, corner, monitor_id, active_window.get("address", ""), debug=False):
                if debug:
                    print(f"    - {corner}: ✗ would bounce")
                continue

            # Calculate position and check for overlap
            pos_x, pos_y = calculate_corner_position(monitor, corner, sneaky_size)
            sneaky_rect = (pos_x, pos_y, sneaky_size[0], sneaky_size[1])

            # Check overlap with all windows to avoid
            overlaps = False
            for window in windows_to_avoid:
                window_rect = (
                    window["at"][0],
                    window["at"][1],
                    window["size"][0],
                    window["size"][1]
                )
                if rectangles_overlap(sneaky_rect, window_rect):
                    overlaps = True
                    if debug:
                        print(f"    - {corner}: ✗ overlaps with {window.get('address', '')[-8:]}")
                    break

            if not overlaps:
                if debug:
                    print(f"  [Alternative] ✓ Found on monitor {monitor_id}: {corner}")
                return (corner, monitor_id)

    if debug:
        print(f"  [Alternative] ✗ No alternative found anywhere!")
    return None


def execute_corner_move(
    sneaky_address: str,
    corner: str,
    target_monitor: Dict,
    current_monitor_id: int,
    sneaky_pinned: bool,
    jump_history: Dict[str, List[Tuple[str, int, str, float]]],
    cooldown_positions: Dict[str, Dict[Tuple[str, int], float]],
    sneaky_window: Dict,
    all_windows: List[Dict],
    active_window: Optional[Dict] = None,
    is_bounce_recovery: bool = False
) -> None:
    """
    Execute a corner move and record it in history.

    Args:
        sneaky_address: Address of the sneaky window
        corner: Target corner name
        target_monitor: Target monitor dict
        current_monitor_id: Current monitor ID
        sneaky_pinned: Whether the window is pinned
        jump_history: Jump history dictionary
        cooldown_positions: Cooldown tracking per window
        sneaky_window: The sneaky window dict (for size)
        all_windows: List of all windows to check what's at target location
        active_window: Optional active window to restore focus to
        is_bounce_recovery: Whether this is a bounce recovery move (triggers cooldown)
    """
    target_monitor_id = target_monitor["id"]

    # Before moving, determine what window is at the target location
    sneaky_size = (sneaky_window["size"][0], sneaky_window["size"][1])
    target_pos_x, target_pos_y = calculate_corner_position(target_monitor, corner, sneaky_size)
    target_rect = (target_pos_x, target_pos_y, sneaky_size[0], sneaky_size[1])

    print(f"  [Target] Corner {corner} on monitor {target_monitor_id}: pos ({target_pos_x}, {target_pos_y}), size {sneaky_size}")

    # Get the target monitor's active workspace (not the sneaky window's workspace)
    target_workspace_id = target_monitor.get("activeWorkspace", {}).get("id") if isinstance(target_monitor.get("activeWorkspace"), dict) else None

    window_at_target = ""
    for window in all_windows:
        if window.get("address") == sneaky_address:
            continue  # Skip the sneaky window itself

        # Only consider windows on the target monitor's active workspace
        window_workspace_id = window.get("workspace", {}).get("id") if isinstance(window.get("workspace"), dict) else window.get("workspace")
        if window_workspace_id != target_workspace_id:
            continue

        window_rect = (
            window["at"][0],
            window["at"][1],
            window["size"][0],
            window["size"][1]
        )
        if rectangles_overlap(target_rect, window_rect):
            window_at_target = window.get("address", "")
            print(f"  [Target] Window at target: {window_at_target[-8:]} (ws {window_workspace_id}) at ({window['at'][0]}, {window['at'][1]}), size ({window['size'][0]}, {window['size'][1]})")
            break  # Take the first overlapping window

    # Now move the window
    if target_monitor_id != current_monitor_id:
        # Move to different monitor
        print(f"Moving to {target_monitor['name']} ({corner})")
        restore_focus = active_window.get("address") if active_window else None
        monitor_movement.move_window_to_monitor_and_corner(
            sneaky_address,
            target_monitor['name'],
            corner,
            sneaky_pinned,
            restore_focus
        )
    else:
        # Same monitor, different corner
        print(f"Moving to {corner} corner")
        move_window_to_corner(sneaky_address, corner)
        # Restore focus
        if active_window and active_window.get("address") != sneaky_address:
            time.sleep(0.05)
            window_manager.focus_window(active_window["address"])

    # Record the jump with the window at the target location
    jump_history[sneaky_address].append((corner, target_monitor_id, window_at_target, time.time()))

    # If this is a bounce recovery, add cooldown for the positions we were bouncing between
    if is_bounce_recovery and window_at_target:
        if sneaky_address not in cooldown_positions:
            cooldown_positions[sneaky_address] = {}

        # Get the recent bounce positions on current monitor and mark them as forbidden for 8 seconds
        bounce_windows = get_bounce_windows(jump_history[sneaky_address], monitor_id=current_monitor_id)
        if bounce_windows:
            current_time = time.time()
            cooldown_expiry = current_time + 8.0

            # Mark recent positions as forbidden
            for corner_name, mon_id, win_addr, _ in jump_history[sneaky_address][-6:]:
                if win_addr in bounce_windows:
                    position = (corner_name, mon_id)
                    cooldown_positions[sneaky_address][position] = cooldown_expiry


def monitor_sneaky_windows(interval: float = 0.5, debug: bool = True, focus_cooldown: float = 1.0):
    """
    Main monitoring loop that keeps sneaky windows away from the active window.

    Args:
        interval: Time in seconds between checks
        debug: Enable debug output for bounce detection
        focus_cooldown: Time in seconds a window must be focused before triggering a move
    """
    print("Starting sneaky window monitor..." + (" (debug mode)" if debug else ""))

    # Track jump history per window: {address: [(corner, monitor_id, window_at_location, timestamp), ...]}
    jump_history = {}

    # Track cooldown positions per window: {address: {(corner, monitor_id): expiry_timestamp}}
    cooldown_positions = {}

    # Track last active window and when it became active
    last_active_address = None
    last_active_time = 0.0

    # Initialize history with current positions of sneaky windows
    initial_sneaky_windows = get_sneaky_windows()
    if initial_sneaky_windows:
        monitors = get_monitors()
        all_windows = run_hyprctl(["clients", "-j"]) or []

        for sneaky in initial_sneaky_windows:
            sneaky_address = sneaky["address"]
            sneaky_monitor_id = sneaky["monitor"]

            # Find current monitor
            current_monitor = next(
                (m for m in monitors if m["id"] == sneaky_monitor_id),
                None
            )

            if current_monitor:
                # Detect current corner
                current_corner = monitor_movement.detect_current_corner(sneaky, monitors)

                # Find which window it's currently overlapping (on current monitor's active workspace)
                sneaky_rect = (
                    sneaky["at"][0],
                    sneaky["at"][1],
                    sneaky["size"][0],
                    sneaky["size"][1]
                )

                current_workspace_id = current_monitor.get("activeWorkspace", {}).get("id") if isinstance(current_monitor.get("activeWorkspace"), dict) else None

                overlapping_window = ""
                for window in all_windows:
                    if window.get("address") == sneaky_address:
                        continue

                    # Only consider windows on the current monitor's active workspace
                    window_workspace_id = window.get("workspace", {}).get("id") if isinstance(window.get("workspace"), dict) else window.get("workspace")
                    if window_workspace_id != current_workspace_id:
                        continue

                    window_rect = (
                        window["at"][0],
                        window["at"][1],
                        window["size"][0],
                        window["size"][1]
                    )
                    if rectangles_overlap(sneaky_rect, window_rect):
                        overlapping_window = window.get("address", "")
                        break

                # Initialize jump history with current position
                jump_history[sneaky_address] = [(current_corner, sneaky_monitor_id, overlapping_window, time.time())]

                if debug:
                    print(f"  [Init] Sneaky window at {current_corner} on monitor {sneaky_monitor_id}, overlapping: {overlapping_window[-8:] if overlapping_window else 'none'}")

    while True:
        try:
            # Get all sneaky windows
            sneaky_windows = get_sneaky_windows()

            if not sneaky_windows:
                # No sneaky windows, just wait
                time.sleep(interval)
                continue

            # Get active window
            active_window = get_active_window()
            if not active_window or not active_window.get("address"):
                time.sleep(interval)
                continue

            # Check focus cooldown - only proceed if window has been focused long enough
            active_address = active_window.get("address")
            current_time = time.time()

            if active_address != last_active_address:
                # New window became active, start the cooldown timer
                last_active_address = active_address
                last_active_time = current_time
                time.sleep(interval)
                continue

            if current_time - last_active_time < focus_cooldown:
                # Window hasn't been active long enough yet
                time.sleep(interval)
                continue

            # Get monitors
            monitors = get_monitors()
            if not monitors:
                time.sleep(interval)
                continue

            # Get all windows for overlap checking
            all_windows = run_hyprctl(["clients", "-j"]) or []

            # Process each sneaky window
            for sneaky in sneaky_windows:
                sneaky_address = sneaky["address"]

                # Skip if the sneaky window is the active window
                if sneaky_address == active_window["address"]:
                    continue

                # Get current position
                sneaky_rect = (
                    sneaky["at"][0],
                    sneaky["at"][1],
                    sneaky["size"][0],
                    sneaky["size"][1]
                )
                active_rect = (
                    active_window["at"][0],
                    active_window["at"][1],
                    active_window["size"][0],
                    active_window["size"][1]
                )

                # Check if they overlap
                if not rectangles_overlap(sneaky_rect, active_rect):
                    # No overlap, all good
                    continue

                # Overlap detected! Find a safe spot
                sneaky_monitor_id = sneaky["monitor"]
                current_monitor = next(
                    (m for m in monitors if m["id"] == sneaky_monitor_id),
                    None
                )

                if not current_monitor:
                    continue

                # Initialize jump history and cooldown for this window if needed
                if sneaky_address not in jump_history:
                    jump_history[sneaky_address] = []
                if sneaky_address not in cooldown_positions:
                    cooldown_positions[sneaky_address] = {}

                # Get current monitor ID early - needed for all paths
                current_monitor_id = current_monitor["id"]

                # Check if there's only one window on this workspace (besides sneaky)
                # If so, skip trying corners and go directly to another monitor
                current_workspace_id = current_monitor.get("activeWorkspace", {}).get("id") if isinstance(current_monitor.get("activeWorkspace"), dict) else None
                workspace_windows = [
                    w for w in all_windows
                    if (w.get("workspace", {}).get("id") if isinstance(w.get("workspace"), dict) else w.get("workspace")) == current_workspace_id
                    and w.get("address") != sneaky_address
                ]

                if len(workspace_windows) <= 1:
                    # Only one window on this workspace - no point trying corners, move to next monitor
                    print(f"Only {len(workspace_windows)} window(s) on workspace {current_workspace_id}, moving to next monitor")
                    # Skip to monitor switch logic
                    safe_corner = None
                else:
                    # Try to find a non-overlapping corner on the current monitor
                    safe_corner = find_non_overlapping_corner(sneaky, active_window, current_monitor)

                if safe_corner:
                    # Check if moving to this corner would create a bounce pattern
                    active_window_address = active_window.get("address", "")

                    if debug:
                        print(f"\n🔍 Checking bounce for corner {safe_corner}:")

                    would_bounce = detect_bounce_pattern(
                        jump_history[sneaky_address],
                        safe_corner,
                        current_monitor_id,
                        active_window_address,
                        debug=debug
                    )

                    if would_bounce:
                        # Find an alternative corner that won't bounce
                        print(f"🔄 Bounce pattern detected, finding alternative...")
                        alternative = find_alternative_corner(
                            sneaky,
                            active_window,
                            current_monitor,
                            monitors,
                            all_windows,
                            jump_history[sneaky_address],
                            cooldown_positions[sneaky_address],
                            safe_corner,
                            debug=debug
                        )

                        if debug and alternative:
                            print(f"  [Alternative] Found: {alternative[0]} on monitor {alternative[1]}")
                        elif debug:
                            print(f"  [Alternative] No alternative found!")

                        if alternative:
                            alt_corner, alt_monitor_id = alternative
                            alt_monitor = next(
                                (m for m in monitors if m["id"] == alt_monitor_id),
                                None
                            )
                            if alt_monitor:
                                # Count jumps on current monitor before switch
                                jumps_on_current_monitor = sum(
                                    1 for _, mon_id, _, _ in jump_history[sneaky_address]
                                    if mon_id == current_monitor_id
                                )
                                if alt_monitor_id != current_monitor_id:
                                    print(f"📊 Monitor switch after {jumps_on_current_monitor} jumps on monitor {current_monitor_id}")

                                execute_corner_move(
                                    sneaky_address,
                                    alt_corner,
                                    alt_monitor,
                                    current_monitor_id,
                                    sneaky.get("pinned", False),
                                    jump_history,
                                    cooldown_positions,
                                    sneaky,
                                    all_windows,
                                    active_window,
                                    is_bounce_recovery=True
                                )
                        else:
                            # No alternative found, use the original safe corner anyway
                            print(f"No alternative found, using {safe_corner} anyway")
                            execute_corner_move(
                                sneaky_address,
                                safe_corner,
                                current_monitor,
                                current_monitor_id,
                                sneaky.get("pinned", False),
                                jump_history,
                                cooldown_positions,
                                sneaky,
                                all_windows,
                                active_window,
                                is_bounce_recovery=False
                            )
                    else:
                        # No bounce pattern, move to safe corner normally
                        execute_corner_move(
                            sneaky_address,
                            safe_corner,
                            current_monitor,
                            current_monitor_id,
                            sneaky.get("pinned", False),
                            jump_history,
                            cooldown_positions,
                            sneaky,
                            all_windows,
                            active_window,
                            is_bounce_recovery=False
                        )
                else:
                    # All corners on current monitor overlap, move to next monitor
                    # Sort monitors by X position
                    sorted_monitors = sorted(monitors, key=lambda m: m["x"])
                    current_index = next(
                        (i for i, m in enumerate(sorted_monitors) if m["id"] == sneaky_monitor_id),
                        None
                    )

                    if current_index is not None:
                        # Try the next monitor (wrap around if needed)
                        next_index = (current_index + 1) % len(sorted_monitors)
                        next_monitor = sorted_monitors[next_index]

                        # Try to find a non-overlapping corner on the target monitor
                        # We need to simulate the window being there to check overlap
                        safe_corner = find_non_overlapping_corner(sneaky, active_window, next_monitor)
                        if not safe_corner:
                            # No safe corner found, default to lower-right
                            safe_corner = "lower-right"

                        print(f"All corners overlap, moving to {next_monitor['name']}")
                        execute_corner_move(
                            sneaky_address,
                            safe_corner,
                            next_monitor,
                            current_monitor_id,
                            sneaky.get("pinned", False),
                            jump_history,
                            cooldown_positions,
                            sneaky,
                            all_windows,
                            active_window,
                            is_bounce_recovery=False
                        )

            time.sleep(interval)

        except KeyboardInterrupt:
            print("\nStopping sneaky window monitor...")
            break
        except Exception as e:
            print(f"Error in monitoring loop: {e}", file=sys.stderr)
            time.sleep(interval)


if __name__ == "__main__":
    monitor_sneaky_windows()
