#!/usr/bin/env python3

import logging
import os
import subprocess
import time

from . import config, window_manager


def configure_logging(debug=False):
    """Configure logging based on debug flag."""
    logging_level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def launch_and_manage(workspace, name, command, is_master, launch_delay=None, no_focus=False):
    """Switch workspace, launch application, and set as master if needed."""
    print(f"Switching to workspace {workspace}")

    # Handle special workspaces differently
    if workspace.startswith("special:"):
        special_name = workspace.replace("special:", "")
        window_manager.toggle_special_workspace(special_name)
    else:
        window_manager.switch_to_workspace(workspace)

    existing_windows = window_manager.get_window_addresses()

    # Replace `___name___` with the actual name
    command = command.replace("___name___", name)

    print(f"Launching: {command}")

    # Ensure proper environment for all launched apps
    env = os.environ.copy()
    # Ensure PATH includes common locations
    if "PATH" in env:
        paths = env["PATH"].split(":")
        if not any(p.endswith("/.local/bin") for p in paths):
            env["PATH"] = f"{env['PATH']}:/home/rash/.local/bin"

    # Start the process with the enhanced environment
    process = subprocess.Popen(command, shell=True, env=env)
    logging.debug(f"Started process for {name} with PID {process.pid}")

    # Wait specifically for this window
    address = window_manager.wait_for_window(existing_windows)
    
    # Use custom launch_delay if provided, otherwise use default
    window_delay = launch_delay if launch_delay is not None else config.WINDOW_CREATION_DELAY
    time.sleep(window_delay)
    if not address:
        logging.warning(f"No window detected for {name} in workspace {workspace}")
        return None  # Return None if window did not appear

    print(f"New window detected at {address}")

    # If no_focus is set, apply nofocus property to this specific window
    if no_focus:
        window_manager.run_hyprctl_command(
            ["dispatch", "setprop", f"address:{address}", "nofocus", "1"]
        )
        logging.debug(f"Set nofocus property for window {address}")

    # If the window is supposed to be master and it's not already, swap it
    if is_master and not window_manager.is_window_master(address, workspace):
        print(f"Swapping {address} to master in workspace {workspace}")
        window_manager.focus_window(address)
        window_manager.run_hyprctl_command(["dispatch", "layoutmsg", "swapwithmaster"])

    return address


def focus_workspace_master(workspace):
    """Focus the master window in a workspace."""
    # Handle special workspaces differently
    if workspace.startswith("special:"):
        special_name = workspace.replace("special:", "")
        window_manager.toggle_special_workspace(special_name)
    else:
        window_manager.switch_to_workspace(workspace)

    master_address = window_manager.get_master_window_address(workspace)
    if master_address:  # Check if master address exists
        window_manager.focus_window(master_address)


def launch_profile_apps(
    profile_name=config.DEFAULT_PROFILE, debug=False, start_fresh=False
):
    """Launch applications for a specific profile."""
    configure_logging(debug)
    logging.info(f"Launching apps for profile: {profile_name}")

    # Initial delay - allow window manager to stabilize
    time.sleep(config.INITIAL_DELAY)

    profile_data = config.APP_PROFILES.get(profile_name)
    if not profile_data:
        logging.error(f"Profile '{profile_name}' not found in APP_PROFILES")
        return

    # Track window addresses that have nofocus set to remove it later
    no_focus_addresses = []

    for workspace, apps in profile_data.items():
        # Skip non-workspace keys like "staging_ws"
        # Allow numeric workspaces (e.g., "1", "12") and special workspaces (e.g., "special:stash-left")
        if not isinstance(workspace, str):
            continue
        if not (workspace.isdigit() or workspace.startswith("special:")):
            continue

        for app in apps:
            address = launch_and_manage(
                workspace,
                app["name"],
                app["command"],
                app["is_master"],
                app.get("launch_delay"),
                app.get("no_focus", False),
            )

            # Track addresses with nofocus for later removal
            if app.get("no_focus", False) and address:
                no_focus_addresses.append(address)

        # Ensure focus stays on the master window for this workspace
        focus_workspace_master(workspace)

    # Remove nofocus property from windows that had it set
    for address in no_focus_addresses:
        window_manager.run_hyprctl_command(
            ["dispatch", "setprop", f"address:{address}", "nofocus", "0"]
        )
        logging.debug(f"Removed nofocus property from window {address}")

    # Return to default workspaces and focus master windows
    # Switch to monitor 2 (HDMI-A-1) workspace
    focus_workspace_master("11")
    time.sleep(config.FOCUS_WS_DELAY)

    # Switch to monitor 1 (DP-1) workspace
    focus_workspace_master("1")

    return 0
