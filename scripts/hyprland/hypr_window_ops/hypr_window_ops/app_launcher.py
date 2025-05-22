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


def launch_and_manage(workspace, name, command, is_master):
    """Switch workspace, launch application, and set as master if needed."""
    print(f"Switching to workspace {workspace}")
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
    time.sleep(config.WINDOW_CREATION_DELAY)
    if not address:
        logging.warning(f"No window detected for {name} in workspace {workspace}")
        return None  # Return None if window did not appear

    print(f"New window detected at {address}")

    # If the window is supposed to be master and it's not already, swap it
    if is_master and not window_manager.is_window_master(address, workspace):
        print(f"Swapping {address} to master in workspace {workspace}")
        window_manager.focus_window(address)
        subprocess.run(["hyprctl", "dispatch", "layoutmsg", "swapwithmaster"])

    return address


def focus_workspace_master(workspace):
    """Focus the master window in a workspace."""
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

    for workspace, apps in profile_data.items():
        # Skip non-workspace keys like "staging_ws"
        if not isinstance(workspace, str) or not workspace.isdigit():
            continue

        for app in apps:
            launch_and_manage(
                workspace,
                app["name"],
                app["command"],
                app["is_master"],
            )

        # Ensure focus stays on the master window for this workspace
        focus_workspace_master(workspace)

    # Return to default workspaces and focus master windows
    # Switch to monitor 2 (DP-2) workspace
    focus_workspace_master("11")
    time.sleep(config.FOCUS_WS_DELAY)

    # Switch to monitor 1 (DP-1) workspace
    focus_workspace_master("1")

    return 0
