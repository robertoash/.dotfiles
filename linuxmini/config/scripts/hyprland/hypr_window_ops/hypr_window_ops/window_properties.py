#!/usr/bin/env python3

import subprocess

from . import snap_windows, window_manager


def run_command(cmd):
    """Run a shell command."""
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)


def get_active_window():
    """Get information about the active window."""
    return window_manager.run_hyprctl(["activewindow", "-j"])


def pin_window_without_dimming():
    """Pin the active window without dimming, toggling if already pinned."""
    active_window = get_active_window()
    window_id = active_window.get("address")
    floating = active_window.get("floating")
    pinned = active_window.get("pinned")

    if pinned:
        # Unpin the window and disable nodim
        window_manager.run_hyprctl_command(["dispatch", "pin"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "0"]
        )
    else:
        # Float the window first if it's not already floating
        if not floating:
            toggle_floating()
        # Pin the window and set nodim property
        window_manager.run_hyprctl_command(["dispatch", "pin"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "1"]
        )
        snap_windows.snap_window_to_corner(corner="lower-right")


def toggle_nofocus():
    """Toggle nofocus property for floating pinned windows."""
    active_window = get_active_window()
    window_id = active_window.get("address")
    floating = active_window.get("floating")
    pinned = active_window.get("pinned")

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


def toggle_floating():
    """Toggle floating state of the active window."""
    active_window = get_active_window()
    floating = active_window.get("floating")

    new_width = "1280"
    new_height = "720"

    if floating:
        # Make the window tiled
        window_manager.run_hyprctl_command(["dispatch", "settiled"])
    else:
        # Float the window and resize
        window_manager.run_hyprctl_command(["dispatch", "setfloating"])
        window_manager.run_hyprctl_command(
            ["dispatch", "resizeactive", "exact", new_width, new_height]
        )


def toggle_fullscreen_without_dimming():
    """Toggle fullscreen without dimming for the active window, managing pinned/floating state."""
    active_window = get_active_window()
    window_id = active_window.get("address")
    fullscreen = active_window.get("fullscreen")
    floating = active_window.get("floating")
    pinned = active_window.get("pinned")

    state_file = "/tmp/fullscreen_window_states"

    if fullscreen:
        # Exit fullscreen and restore previous state
        window_manager.run_hyprctl_command(["dispatch", "fullscreen"])
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
                    window_manager.run_hyprctl_command(["dispatch", "setfloating"])
                elif not saved_state["floating"] and floating:
                    window_manager.run_hyprctl_command(["dispatch", "settiled"])

                # Restore pinned state
                if saved_state["pinned"] and not pinned:
                    window_manager.run_hyprctl_command(["dispatch", "pin"])
                elif not saved_state["pinned"] and pinned:
                    window_manager.run_hyprctl_command(["dispatch", "pin"])

                # Remove this window from the state file
                del states[window_id]
                with open(state_file, "w") as f:
                    for addr, state in states.items():
                        f.write(f"{addr}:{state['floating']}:{state['pinned']}\n")
            else:
                # Default to tiled (no pin) if no previous state found
                if floating:
                    window_manager.run_hyprctl_command(["dispatch", "settiled"])
                if pinned:
                    window_manager.run_hyprctl_command(["dispatch", "pin"])

        except FileNotFoundError:
            # Default to tiled (no pin) if no state file found
            if floating:
                window_manager.run_hyprctl_command(["dispatch", "settiled"])
            if pinned:
                window_manager.run_hyprctl_command(["dispatch", "pin"])
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
            # Focus the window first to ensure it's active
            window_manager.run_hyprctl_command(
                ["dispatch", "focuswindow", f"address:{window_id}"]
            )
            window_manager.run_hyprctl_command(["dispatch", "pin"])

            # Re-get window state after unpinning to verify the change
            active_window = get_active_window()
            window_id = active_window.get("address")
            new_pinned = active_window.get("pinned")
            print(f"Debug: After unpinning, pinned state is: {new_pinned}")

        # Ensure window is focused before fullscreen
        window_manager.run_hyprctl_command(
            ["dispatch", "focuswindow", f"address:{window_id}"]
        )

        # Enter fullscreen and set nodim property
        window_manager.run_hyprctl_command(["dispatch", "fullscreen"])
        window_manager.run_hyprctl_command(
            ["setprop", f"address:{window_id}", "nodim", "1"]
        )
