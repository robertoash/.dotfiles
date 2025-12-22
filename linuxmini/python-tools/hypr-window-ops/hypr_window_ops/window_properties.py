#!/usr/bin/env python3

import subprocess

from . import snap_windows, window_manager


def run_command(cmd):
    """Run a shell command."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def get_active_window():
    """Get information about the active window."""
    return window_manager.run_hyprctl(["activewindow", "-j"])


def pin_window_without_dimming(relative_floating=False):
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
    else:
        # Float the window first if it's not already floating
        if not floating:
            window_manager.run_hyprctl_command(["dispatch", "setfloating", f"address:{window_id}"])
            # Re-fetch window info after floating to get updated state
            window_info = window_manager.get_target_window(relative_floating)
            window_id = window_info.get("address")
        # Pin the window and set nodim property
        window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "1"]
        )
        snap_windows.snap_window_to_corner(
            corner="lower-right", window_address=window_id
        )


def toggle_nofocus(relative_floating=False):
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


def toggle_floating(relative_floating=False):
    """Toggle floating state of a window."""
    active_window = get_active_window()
    is_currently_floating = active_window.get("floating", False)

    if is_currently_floating:
        # Deactivating floating -> tiled: use smart targeting
        window_info = window_manager.get_target_window(relative_floating)
        window_id = window_info.get("address")
        window_manager.run_hyprctl_command(["dispatch", "settiled", f"address:{window_id}"])
    else:
        # Activating tiled -> floating: always use active window
        window_info = window_manager.get_target_window(
            relative_floating, for_toggle_floating_activation=True
        )
        window_id = window_info.get("address")
        new_width = "1280"
        new_height = "720"
        window_manager.run_hyprctl_command(["dispatch", "setfloating", f"address:{window_id}"])
        window_manager.run_hyprctl_command(
            ["dispatch", "resizeactive", "exact", new_width, new_height]
        )


def toggle_double_size(relative_floating=False):
    """Toggle double size of a floating window."""
    # Get target window without changing focus
    window_info = window_manager.get_target_window(relative_floating)
    if not window_info:
        print("❌ Could not find window")
        return

    window_id = window_info.get("address")
    floating = window_info.get("floating")

    # Check if window is floating
    if not floating:
        print("🚫 Window is not floating. Cannot toggle double size.")
        return

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
            # Window is doubled, restore original size and position
            orig_state = doubled_states[window_id]

            # Resize using resizewindowpixel with address (no focus change needed)
            window_manager.run_hyprctl_command([
                "dispatch", "resizewindowpixel",
                f"exact {orig_state['width']} {orig_state['height']},address:{window_id}"
            ])

            # Restore original position
            x_offset = orig_state["x"] - current_x
            y_offset = orig_state["y"] - current_y
            if x_offset != 0 or y_offset != 0:
                window_manager.run_hyprctl_command([
                    "dispatch", "movewindowpixel",
                    "--",
                    f"{x_offset} {y_offset},address:{window_id}"
                ])

            # Remove from state file
            del doubled_states[window_id]
            with open(state_file, "w") as f:
                for addr, state in doubled_states.items():
                    f.write(f"{addr}:{state['width']}:{state['height']}:{state['x']}:{state['y']}\n")

            print(f"✅ Window restored to {orig_state['width']}x{orig_state['height']}")
        else:
            # Window is not doubled, double it and save original size/position
            # Detect which corner the window is in
            corner = snap_windows.detect_current_corner(window_info)

            new_width = current_width * 2
            new_height = current_height * 2

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

            # Calculate offset to keep corner in place
            # Default resize grows from top-left, so we need to compensate
            x_offset = 0
            y_offset = 0

            if corner in ["upper-right", "lower-right"]:
                x_offset = -current_width
            if corner in ["lower-left", "lower-right"]:
                y_offset = -current_height

            # Apply offset if needed to anchor the corner
            if x_offset != 0 or y_offset != 0:
                window_manager.run_hyprctl_command([
                    "dispatch", "movewindowpixel",
                    "--",
                    f"{x_offset} {y_offset},address:{window_id}"
                ])

            print(f"✅ Window doubled to {new_width}x{new_height} (anchored at {corner})")

    except FileNotFoundError:
        # No state file exists, so window isn't doubled - double it
        # Detect which corner the window is in
        corner = snap_windows.detect_current_corner(window_info)

        new_width = current_width * 2
        new_height = current_height * 2

        with open(state_file, "w") as f:
            f.write(f"{window_id}:{current_width}:{current_height}:{current_x}:{current_y}\n")

        # Resize using resizewindowpixel with address (no focus change needed)
        window_manager.run_hyprctl_command([
            "dispatch", "resizewindowpixel",
            f"exact {new_width} {new_height},address:{window_id}"
        ])

        # Calculate offset to keep corner in place
        x_offset = 0
        y_offset = 0

        if corner in ["upper-right", "lower-right"]:
            x_offset = -current_width
        if corner in ["lower-left", "lower-right"]:
            y_offset = -current_height

        # Apply offset if needed to anchor the corner
        if x_offset != 0 or y_offset != 0:
            window_manager.run_hyprctl_command([
                "dispatch", "movewindowpixel",
                "--",
                f"{x_offset} {y_offset},address:{window_id}"
            ])

        print(f"✅ Window doubled to {new_width}x{new_height} (anchored at {corner})")


def toggle_fullscreen_without_dimming(relative_floating=False):
    """Toggle fullscreen without dimming, managing pinned/floating state."""
    window_info = window_manager.get_target_window(relative_floating)
    window_id = window_info.get("address")
    fullscreen = window_info.get("fullscreen")
    floating = window_info.get("floating")
    pinned = window_info.get("pinned")

    state_file = "/tmp/fullscreen_window_states"

    if fullscreen:
        # Exit fullscreen and restore previous state
        window_manager.run_hyprctl_command(["dispatch", "fullscreen", f"address:{window_id}"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "0"]
        )

        # Restore previous state
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
                            states[addr] = {
                                "floating": was_floating,
                                "pinned": was_pinned,
                            }

            if window_id in states:
                saved_state = states[window_id]

                # Restore floating state first
                if saved_state["floating"] and not floating:
                    window_manager.run_hyprctl_command(["dispatch", "setfloating", f"address:{window_id}"])
                elif not saved_state["floating"] and floating:
                    window_manager.run_hyprctl_command(["dispatch", "settiled", f"address:{window_id}"])

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
                if pinned:
                    window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])

        except FileNotFoundError:
            # Default to tiled (no pin) if no state file found
            if floating:
                window_manager.run_hyprctl_command(["dispatch", "settiled", f"address:{window_id}"])
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
                            existing_states[addr] = {
                                "floating": was_floating,
                                "pinned": was_pinned,
                            }
        except FileNotFoundError:
            pass

        # Add current window state
        existing_states[window_id] = {"floating": floating, "pinned": pinned}

        # Write all states back
        with open(state_file, "w") as f:
            for addr, state in existing_states.items():
                f.write(f"{addr}:{state['floating']}:{state['pinned']}\n")

        # Unpin if pinned before going fullscreen
        if pinned:
            window_manager.run_hyprctl_command(["dispatch", "pin", f"address:{window_id}"])

        # Enter fullscreen and set nodim property
        window_manager.run_hyprctl_command(["dispatch", "fullscreen", f"address:{window_id}"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "1"]
        )
