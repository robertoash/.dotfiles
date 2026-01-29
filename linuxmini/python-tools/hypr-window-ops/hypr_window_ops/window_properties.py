#!/usr/bin/env python3

import subprocess
import time

from . import monitor_utils, snap_windows, window_manager


def run_command(cmd):
    """Run a shell command."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def get_active_window():
    """Get information about the active window."""
    return window_manager.run_hyprctl(["activewindow", "-j"])


def pin_window_without_dimming(relative_floating=False, sneaky=False):
    """Pin a floating window without dimming, toggling if already pinned."""
    window_info = window_manager.get_target_window(relative_floating)
    window_id = window_info.get("address")
    floating = window_info.get("floating")
    pinned = window_info.get("pinned")

    if pinned:
        # Unpin the window and disable nodim
        window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "0"]
        )
        # Remove sneaky tag when unpinning
        if sneaky:
            window_manager.remove_tag(window_id, "sneaky")
    else:
        # Float the window first if it's not already floating
        if not floating:
            window_manager.run_hyprctl_command(["dispatch", "setfloating", f"address:{window_id}"])
            time.sleep(0.05)  # Allow Hyprland to sync floating state before re-fetching
            # Re-fetch window info after floating to get updated state
            window_info = window_manager.get_target_window(relative_floating)
            window_id = window_info.get("address")

        # Detect current corner before resizing
        current_corner = monitor_utils.detect_window_corner(window_info)
        target_corner = current_corner if current_corner else "lower-left"

        # Resize to 1228x691 (16:9, doubles to 2456x1382 to match master window width)
        window_manager.run_hyprctl_command([
            "dispatch", "resizewindowpixel",
            f"exact 1228 691,address:{window_id}"
        ])
        # Pin the window and set nodim property
        window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "1"]
        )
        snap_windows.snap_window_to_corner(
            corner=target_corner, window_address=window_id
        )
        # Apply sneaky tag if requested
        if sneaky:
            window_manager.apply_tag(window_id, "sneaky")


def toggle_nofocus(relative_floating=False, sneaky=False):
    """Toggle nofocus property for floating pinned windows."""
    window_info = window_manager.get_target_window(relative_floating)
    window_id = window_info.get("address")
    floating = window_info.get("floating")
    pinned = window_info.get("pinned")

    if floating and pinned:
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nofocus", "1"]
        )
        # append window_id to nofocus_windows file
        with open("/tmp/nofocus_windows", "a") as f:
            f.write(window_id + "\n")
        # Apply sneaky tag if requested
        if sneaky:
            window_manager.apply_tag(window_id, "sneaky")
    else:
        try:
            # get nofocus_windows from file
            with open("/tmp/nofocus_windows") as f:
                nofocus_windows = f.read().splitlines()

            if not nofocus_windows:
                # Failsafe: If the file is empty, run `setprop nofocus 0` on every client
                all_clients = window_manager.get_clients()
                for client in all_clients:
                    window_manager.run_hyprctl_command(
                        ["setprop", f"address:{client['address']}", "nofocus", "0"]
                    )
            else:
                updated_windows = []
                for window in nofocus_windows:
                    success = window_manager.run_hyprctl_command(
                        ["setprop", f"address:{window}", "nofocus", "0"]
                    )
                    if not success:
                        updated_windows.append(window)

                # Rewrite the file with windows that were not successfully updated
                with open("/tmp/nofocus_windows", "w") as f:
                    f.write("\n".join(updated_windows))

        except FileNotFoundError:
            pass  # If the file doesn't exist, there's nothing to do


def toggle_floating(relative_floating=False, sneaky=False):
    """Toggle floating state of a window."""
    active_window = get_active_window()
    is_currently_floating = active_window.get("floating", False)

    if is_currently_floating:
        # Deactivating floating -> tiled: use smart targeting
        window_info = window_manager.get_target_window(relative_floating)
        window_id = window_info.get("address")
        window_manager.run_hyprctl_command(["dispatch", "settiled", f"address:{window_id}"])
        time.sleep(0.05)  # Allow Hyprland to sync state
        # Remove sneaky tag when switching to tiled
        if sneaky:
            window_manager.remove_tag(window_id, "sneaky")
    else:
        # Activating tiled -> floating: always use active window
        window_info = window_manager.get_target_window(
            relative_floating, for_toggle_floating_activation=True
        )
        window_id = window_info.get("address")
        new_width = "1228"
        new_height = "691"
        window_manager.run_hyprctl_command(["dispatch", "setfloating", f"address:{window_id}"])
        time.sleep(0.05)  # Allow Hyprland to sync floating state before subsequent operations
        window_manager.run_hyprctl_command(
            ["dispatch", "resizeactive", "exact", new_width, new_height]
        )
        # Apply sneaky tag if requested
        if sneaky:
            window_manager.apply_tag(window_id, "sneaky")


def toggle_double_size(relative_floating=False, sneaky=False):
    """Toggle double size of a floating window."""
    # Get target window without changing focus
    window_info = window_manager.get_target_window(relative_floating)
    if not window_info:
        print("❌ Could not find window")
        return

    window_id = window_info.get("address")
    floating = window_info.get("floating")
    window_class = window_info.get("class", "").lower()

    # Check if window is floating
    if not floating:
        print("🚫 Window is not floating. Cannot toggle double size.")
        return

    # Apply sneaky tag if requested and floating
    if sneaky and floating:
        window_manager.apply_tag(window_id, "sneaky")

    current_width = window_info["size"][0]
    current_height = window_info["size"][1]
    current_x = window_info["at"][0]
    current_y = window_info["at"][1]

    state_file = "/tmp/doubled_window_sizes"

    # Check if window is currently doubled
    try:
        with open(state_file, "r") as f:
            doubled_states = {}
            for line in f:
                if line.strip():
                    parts = line.strip().split(":")
                    if len(parts) >= 5:
                        addr, orig_w, orig_h, orig_x, orig_y = (
                            parts[0], int(parts[1]), int(parts[2]),
                            int(parts[3]), int(parts[4])
                        )
                        doubled_states[addr] = {
                            "width": orig_w, "height": orig_h,
                            "x": orig_x, "y": orig_y
                        }

        if window_id in doubled_states:
            # Window is doubled, restore original size
            orig_state = doubled_states[window_id]

            # Detect current corner (where window is NOW, not where it was originally)
            current_corner = monitor_utils.detect_window_corner(window_info)

            # Resize using resizewindowpixel with address (no focus change needed)
            window_manager.run_hyprctl_command([
                "dispatch", "resizewindowpixel",
                f"exact {orig_state['width']} {orig_state['height']},address:{window_id}"
            ])

            # Snap to current corner (or center if not snapped)
            if current_corner:
                snap_windows.snap_window_to_corner(
                    corner=current_corner,
                    window_address=window_id
                )
                print(f"✅ Window restored to {orig_state['width']}x{orig_state['height']} and snapped to {current_corner}")
            else:
                print(f"✅ Window restored to {orig_state['width']}x{orig_state['height']}")

            # Remove from state file
            del doubled_states[window_id]
            with open(state_file, "w") as f:
                for addr, state in doubled_states.items():
                    f.write(f"{addr}:{state['width']}:{state['height']}:{state['x']}:{state['y']}\n")

            # Remove large-video tag for mpv/vlc windows when un-doubling
            if "mpv" in window_class or "vlc" in window_class:
                window_manager.remove_tag(window_id, "large-video")
        else:
            # Window is not doubled, double it and save original size/position
            # Detect which corner the window is snapped to (if any)
            corner = monitor_utils.detect_window_corner(window_info)

            # Get monitor info for bounds checking
            monitor = monitor_utils.get_monitor_with_transform(window_info)
            if not monitor:
                print("❌ Could not determine window's monitor")
                return

            # Get usable area using shared utilities
            usable_area = monitor_utils.get_monitor_usable_area(monitor)
            usable_min_x = usable_area["min_x"]
            usable_min_y = usable_area["min_y"]
            usable_max_x = usable_area["max_x"]
            usable_max_y = usable_area["max_y"]

            # Calculate max available size
            max_available_width = usable_max_x - usable_min_x
            max_available_height = usable_max_y - usable_min_y

            # Calculate doubled size, maintaining aspect ratio if capped
            target_width = current_width * 2
            target_height = current_height * 2

            # Calculate scale factors needed to fit
            width_scale = max_available_width / target_width if target_width > max_available_width else 1.0
            height_scale = max_available_height / target_height if target_height > max_available_height else 1.0

            # Use the most restrictive scale to maintain aspect ratio
            scale = min(width_scale, height_scale)

            new_width = int(target_width * scale)
            new_height = int(target_height * scale)

            doubled_states[window_id] = {
                "width": current_width, "height": current_height,
                "x": current_x, "y": current_y
            }

            with open(state_file, "w") as f:
                for addr, state in doubled_states.items():
                    f.write(f"{addr}:{state['width']}:{state['height']}:{state['x']}:{state['y']}\n")

            # Resize using resizewindowpixel with address (no focus change needed)
            window_manager.run_hyprctl_command([
                "dispatch", "resizewindowpixel",
                f"exact {new_width} {new_height},address:{window_id}"
            ])

            # Calculate offset based on anchoring strategy
            x_offset = 0
            y_offset = 0

            if corner:
                # Window is snapped to a corner - anchor at that corner
                # Offset by the actual size increase to keep corner in place
                width_increase = new_width - current_width
                height_increase = new_height - current_height

                if corner in ["upper-right", "lower-right"]:
                    x_offset = -width_increase
                if corner in ["lower-left", "lower-right"]:
                    y_offset = -height_increase
                anchor_type = f"corner: {corner}"
            else:
                # Window is not snapped - anchor at center
                # Offset by half the size increase to keep center in the same position
                width_increase = new_width - current_width
                height_increase = new_height - current_height
                x_offset = -width_increase // 2
                y_offset = -height_increase // 2
                anchor_type = "center"

            # Calculate new position after offset
            new_x = current_x + x_offset
            new_y = current_y + y_offset
            new_right = new_x + new_width
            new_bottom = new_y + new_height

            # Clamp to monitor bounds, but respect corner anchoring
            # When corner-anchored, don't clamp the anchored edges
            if corner:
                # Only clamp the edges opposite to the anchored corner
                if corner in ["upper-left", "lower-left"]:
                    # Left is anchored, only check right
                    if new_right > usable_max_x:
                        x_offset -= (new_right - usable_max_x)
                else:  # upper-right, lower-right
                    # Right is anchored, only check left
                    if new_x < usable_min_x:
                        x_offset += (usable_min_x - new_x)

                if corner in ["upper-left", "upper-right"]:
                    # Top is anchored, only check bottom
                    if new_bottom > usable_max_y:
                        y_offset -= (new_bottom - usable_max_y)
                else:  # lower-left, lower-right
                    # Bottom is anchored, only check top
                    if new_y < usable_min_y:
                        y_offset += (usable_min_y - new_y)
            else:
                # No corner anchor (center mode), clamp all edges
                if new_x < usable_min_x:
                    x_offset += (usable_min_x - new_x)
                elif new_right > usable_max_x:
                    x_offset -= (new_right - usable_max_x)

                if new_y < usable_min_y:
                    y_offset += (usable_min_y - new_y)
                elif new_bottom > usable_max_y:
                    y_offset -= (new_bottom - usable_max_y)

            # Apply offset if needed
            if x_offset != 0 or y_offset != 0:
                window_manager.run_hyprctl_command([
                    "dispatch", "movewindowpixel",
                    "--",
                    f"{x_offset} {y_offset},address:{window_id}"
                ])

            # Apply large-video tag for mpv/vlc windows when doubling
            if "mpv" in window_class or "vlc" in window_class:
                window_manager.apply_tag(window_id, "large-video")

            print(f"✅ Window doubled to {new_width}x{new_height} (anchored at {anchor_type})")

    except FileNotFoundError:
        # No state file exists, so window isn't doubled - double it
        # Detect which corner the window is snapped to (if any)
        corner = monitor_utils.detect_window_corner(window_info)

        # Get monitor info for bounds checking
        monitor = monitor_utils.get_monitor_with_transform(window_info)
        if not monitor:
            print("❌ Could not determine window's monitor")
            return

        # Get usable area using shared utilities
        usable_area = monitor_utils.get_monitor_usable_area(monitor)
        usable_min_x = usable_area["min_x"]
        usable_min_y = usable_area["min_y"]
        usable_max_x = usable_area["max_x"]
        usable_max_y = usable_area["max_y"]

        # Calculate max available size
        max_available_width = usable_max_x - usable_min_x
        max_available_height = usable_max_y - usable_min_y

        # Calculate doubled size, maintaining aspect ratio if capped
        target_width = current_width * 2
        target_height = current_height * 2

        # Calculate scale factors needed to fit
        width_scale = max_available_width / target_width if target_width > max_available_width else 1.0
        height_scale = max_available_height / target_height if target_height > max_available_height else 1.0

        # Use the most restrictive scale to maintain aspect ratio
        scale = min(width_scale, height_scale)

        new_width = int(target_width * scale)
        new_height = int(target_height * scale)

        with open(state_file, "w") as f:
            f.write(f"{window_id}:{current_width}:{current_height}:{current_x}:{current_y}\n")

        # Resize using resizewindowpixel with address (no focus change needed)
        window_manager.run_hyprctl_command([
            "dispatch", "resizewindowpixel",
            f"exact {new_width} {new_height},address:{window_id}"
        ])

        # Calculate offset based on anchoring strategy
        x_offset = 0
        y_offset = 0

        if corner:
            # Window is snapped to a corner - anchor at that corner
            # Offset by the actual size increase to keep corner in place
            width_increase = new_width - current_width
            height_increase = new_height - current_height

            if corner in ["upper-right", "lower-right"]:
                x_offset = -width_increase
            if corner in ["lower-left", "lower-right"]:
                y_offset = -height_increase
            anchor_type = f"corner: {corner}"
        else:
            # Window is not snapped - anchor at center
            # Offset by half the size increase to keep center in the same position
            width_increase = new_width - current_width
            height_increase = new_height - current_height
            x_offset = -width_increase // 2
            y_offset = -height_increase // 2
            anchor_type = "center"

        # Calculate new position after offset
        new_x = current_x + x_offset
        new_y = current_y + y_offset
        new_right = new_x + new_width
        new_bottom = new_y + new_height

        # Clamp to monitor bounds, but respect corner anchoring
        # When corner-anchored, don't clamp the anchored edges
        if corner:
            # Only clamp the edges opposite to the anchored corner
            if corner in ["upper-left", "lower-left"]:
                # Left is anchored, only check right
                if new_right > usable_max_x:
                    x_offset -= (new_right - usable_max_x)
            else:  # upper-right, lower-right
                # Right is anchored, only check left
                if new_x < usable_min_x:
                    x_offset += (usable_min_x - new_x)

            if corner in ["upper-left", "upper-right"]:
                # Top is anchored, only check bottom
                if new_bottom > usable_max_y:
                    y_offset -= (new_bottom - usable_max_y)
            else:  # lower-left, lower-right
                # Bottom is anchored, only check top
                if new_y < usable_min_y:
                    y_offset += (usable_min_y - new_y)
        else:
            # No corner anchor (center mode), clamp all edges
            if new_x < usable_min_x:
                x_offset += (usable_min_x - new_x)
            elif new_right > usable_max_x:
                x_offset -= (new_right - usable_max_x)

            if new_y < usable_min_y:
                y_offset += (usable_min_y - new_y)
            elif new_bottom > usable_max_y:
                y_offset -= (new_bottom - usable_max_y)

        # Apply offset if needed
        if x_offset != 0 or y_offset != 0:
            window_manager.run_hyprctl_command([
                "dispatch", "movewindowpixel",
                "--",
                f"{x_offset} {y_offset},address:{window_id}"
            ])

        # Apply large-video tag for mpv/vlc windows when doubling
        if "mpv" in window_class or "vlc" in window_class:
            window_manager.apply_tag(window_id, "large-video")

        print(f"✅ Window doubled to {new_width}x{new_height} (anchored at {anchor_type})")


def toggle_sneaky_tag(relative_floating=False):
    """Toggle sneaky tag on a window without modifying its state."""
    window_info = window_manager.get_target_window(relative_floating)
    window_id = window_info.get("address")

    # Check if window has sneaky tag
    has_sneaky = "sneaky" in window_info.get("tags", [])

    if has_sneaky:
        # Remove sneaky tag
        window_manager.remove_tag(window_id, "sneaky")
        print("✅ Sneaky tag removed")
    else:
        # Add sneaky tag
        window_manager.apply_tag(window_id, "sneaky")
        print("✅ Sneaky tag applied")


def toggle_fullscreen_without_dimming(relative_floating=False, sneaky=False):
    """Toggle fullscreen without dimming, managing pinned/floating state."""
    # Store original active window to restore focus later
    original_active = window_manager.run_hyprctl(["activewindow", "-j"])
    original_address = original_active.get("address") if original_active else None
    original_monitor = original_active.get("monitor") if original_active else None

    window_info = window_manager.get_target_window(relative_floating)
    window_id = window_info.get("address")
    target_monitor = window_info.get("monitor")
    fullscreen = window_info.get("fullscreen")
    floating = window_info.get("floating")
    pinned = window_info.get("pinned")

    state_file = "/tmp/fullscreen_window_states"

    # Apply sneaky tag if requested and floating
    if sneaky and floating:
        window_manager.apply_tag(window_id, "sneaky")

    should_restore_focus = False
    if fullscreen:
        # Exit fullscreen and restore previous state
        # Focus the window first, then toggle fullscreen (fullscreen doesn't accept address selectors)
        window_manager.run_hyprctl_command(["dispatch", "focuswindow", f"address:{window_id}"])
        window_manager.run_hyprctl_command(["dispatch", "fullscreen"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "0"]
        )
        # Always restore focus when exiting fullscreen
        should_restore_focus = True

        # Restore previous state
        saved_original_address = None
        try:
            with open(state_file, "r") as f:
                states = {}
                for line in f:
                    if line.strip():
                        parts = line.strip().split(":")
                        if len(parts) >= 3:
                            addr, was_floating, was_pinned = (
                                parts[0],
                                parts[1] == "True",
                                parts[2] == "True",
                            )
                            # Also read original_address if present (4th field)
                            original_addr = parts[3] if len(parts) >= 4 and parts[3] else None
                            states[addr] = {
                                "floating": was_floating,
                                "pinned": was_pinned,
                                "original_address": original_addr,
                            }

            if window_id in states:
                saved_state = states[window_id]
                saved_original_address = saved_state.get("original_address")

                # Restore floating state first
                if saved_state["floating"] and not floating:
                    window_manager.run_hyprctl_command(["dispatch", "setfloating", f"address:{window_id}"])
                    time.sleep(0.05)  # Allow Hyprland to sync state
                elif not saved_state["floating"] and floating:
                    window_manager.run_hyprctl_command(["dispatch", "settiled", f"address:{window_id}"])
                    time.sleep(0.05)  # Allow Hyprland to sync state

                # Restore pinned state
                if saved_state["pinned"] and not pinned:
                    window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])
                elif not saved_state["pinned"] and pinned:
                    window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])

                # Remove this window from the state file
                del states[window_id]
                with open(state_file, "w") as f:
                    for addr, state in states.items():
                        f.write(f"{addr}:{state['floating']}:{state['pinned']}\n")
            else:
                # Default to tiled (no pin) if no previous state found
                if floating:
                    window_manager.run_hyprctl_command(["dispatch", "settiled", f"address:{window_id}"])
                    time.sleep(0.05)  # Allow Hyprland to sync state
                if pinned:
                    window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])

        except FileNotFoundError:
            # Default to tiled (no pin) if no state file found
            if floating:
                window_manager.run_hyprctl_command(["dispatch", "settiled", f"address:{window_id}"])
                time.sleep(0.05)  # Allow Hyprland to sync state
            if pinned:
                window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])
    else:
        # Save current state before going fullscreen
        # Read existing states
        existing_states = {}
        try:
            with open(state_file, "r") as f:
                for line in f:
                    if line.strip():
                        parts = line.strip().split(":")
                        if len(parts) >= 3:
                            addr, was_floating, was_pinned = (
                                parts[0],
                                parts[1] == "True",
                                parts[2] == "True",
                            )
                            # Also read original_address if present (4th field)
                            original_addr = parts[3] if len(parts) >= 4 else None
                            existing_states[addr] = {
                                "floating": was_floating,
                                "pinned": was_pinned,
                                "original_address": original_addr,
                            }
        except FileNotFoundError:
            pass

        # Add current window state, including the original active window
        existing_states[window_id] = {
            "floating": floating,
            "pinned": pinned,
            "original_address": original_address if original_address != window_id else None
        }

        # Write all states back
        with open(state_file, "w") as f:
            for addr, state in existing_states.items():
                orig_addr = state.get('original_address', '') or ''
                f.write(f"{addr}:{state['floating']}:{state['pinned']}:{orig_addr}\n")

        # Unpin if pinned before going fullscreen
        if pinned:
            window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])

        # Enter fullscreen and set nodim property
        # Focus the window first, then toggle fullscreen (fullscreen doesn't accept address selectors)
        window_manager.run_hyprctl_command(["dispatch", "focuswindow", f"address:{window_id}"])
        window_manager.run_hyprctl_command(["dispatch", "fullscreen"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "1"]
        )
        # Only restore focus when entering fullscreen if the window is on a different monitor
        # (otherwise focusing back will exit the fullscreen)
        if original_monitor != target_monitor:
            should_restore_focus = True

    # Restore focus to the original active window if needed
    # When exiting fullscreen, use saved_original_address if available (from when we entered fullscreen)
    # When entering fullscreen, use current original_address
    restore_to_address = saved_original_address if 'saved_original_address' in locals() and saved_original_address else original_address
    if should_restore_focus and relative_floating and restore_to_address and restore_to_address != window_id:
        window_manager.run_hyprctl_command(["dispatch", "focuswindow", f"address:{restore_to_address}"])
