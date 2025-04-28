#!/usr/bin/env python3
import argparse
import json
import logging
import os
import subprocess
import sys
import time

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

vars = {
    "CONFIG_DIR": os.environ.get("DOTFILES_DIR", "/home/rash/.config"),
    "CURRENT_PROJECT_DIR": os.environ.get(
        "CURRENT_PROJECT_DIR", "/home/rash/dev/apps/"
    ),
}

# Define common arguments
WAYLAND_ARGS = "--enable-features=UseOzonePlatform --ozone-platform=wayland"
NEW_WINDOW_ARGS = f"--new-window {WAYLAND_ARGS}"
CURSOR_CURRENT_PROJECT_WORKSPACE = (
    "/home/rash/insync/j.roberto.ash@gmail.com/Google\\ Drive/"
    "Dev_cloud/cursor/apps.code-workspace"
)
CURSOR_CONFIG_WORKSPACE = (
    "/home/rash/insync/j.roberto.ash@gmail.com/Google\\ Drive/"
    "Dev_cloud/cursor/dotfiles.code-workspace"
)

# Define applications with name placeholders
APPS = {
    "1": [
        {
            "name": "browser_personal",
            "command": "vivaldi_launch --profile rash",
            "is_master": True,
        },
        {
            "name": "browser_terminal",
            "command": "kitty --title ___name___",
            "is_master": False,
        },
    ],
    "2": [
        {
            "name": "browser_jobhunt",
            "command": "vivaldi_launch --profile jobhunt",
            "is_master": True,
        },
    ],
    "3": [
        {
            "name": "cursor_dev",
            "command": (
                f"cursor {NEW_WINDOW_ARGS} "
                f"--file-uri {CURSOR_CURRENT_PROJECT_WORKSPACE}"
            ),
            "is_master": True,
        },
        {
            "name": "dev_terminal",
            "command": (
                f"kitty --title ___name___ "
                f"--working-directory {vars['CURRENT_PROJECT_DIR']}"
            ),
            "is_master": False,
        },
    ],
    "4": [
        {
            "name": "cursor",
            "command": f"cursor {NEW_WINDOW_ARGS} --file-uri {CURSOR_CONFIG_WORKSPACE}",
            "is_master": True,
        },
        {
            "name": "config_terminal",
            "command": (
                f"kitty --title ___name___ --working-directory {vars['CONFIG_DIR']}"
            ),
            "is_master": False,
        },
    ],
    "5": [
        {
            "name": "nvim",
            "command": "kitty --hold --title ___name___ -e nvim",
            "is_master": True,
        },
        {
            "name": "nvim_terminal",
            "command": (
                f"kitty --title ___name___ --working-directory {vars['CONFIG_DIR']}"
            ),
            "is_master": False,
        },
    ],
    "11": [
        {
            "name": "gpt_zen",
            "command": "vivaldi_launch --profile chatgpt",
            "is_master": True,
        },
        {
            "name": "gpt_terminal",
            "command": "kitty --title ___name___",
            "is_master": False,
        },
    ],
    "12": [
        {
            "name": "obsidian",
            "command": f"env OBSIDIAN_USE_WAYLAND=1 obsidian {WAYLAND_ARGS}",
            "is_master": True,
        },
        {
            "name": "obsidian_terminal",
            "command": "kitty --title ___name___",
            "is_master": False,
        },
    ],
    "13": [
        {
            "name": "perplexity_terminal",
            "command": "kitty --title ___name___",
            "is_master": True,
        },
        {
            "name": "perplexity_zen",
            "command": "vivaldi_launch --profile perplexity",
            "is_master": False,
        },
    ],
}


def configure_logging(args):
    # Configure logging
    logging_utils.configure_logging()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)


def get_window_addresses():
    """Retrieve the set of current window addresses."""
    try:
        clients = json.loads(subprocess.check_output(["hyprctl", "clients", "-j"]))
        return {client["address"] for client in clients}
    except subprocess.CalledProcessError:
        return set()


def is_window_master(window_address, workspace):
    """Check if the given window is already the master window."""
    try:
        master_window = get_master_window_address(workspace)
        if not master_window:
            return False

        return master_window == window_address

    except Exception as e:
        print(f"Error validating master window: {e}")
        return False


def get_master_window_address(workspace):
    """Get the address of the master window for a given workspace."""
    try:
        clients_in_workspace = json.loads(
            subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
        )
        workspace_clients = [
            c
            for c in clients_in_workspace
            if c.get("workspace", {}).get("id") == int(workspace)
        ]

        if not workspace_clients:
            return False

        # Find the master window: sort by at[0] first, then at[1] as a tiebreaker
        master_window = min(
            workspace_clients,
            key=lambda w: (
                w.get("at", [float("inf"), float("inf")])[0],
                w.get("at", [float("inf"), float("inf")])[1],
            ),
        )

        return master_window.get("address")

    except Exception as e:
        print(f"Error checking master window: {e}")
        return False


def wait_for_window(existing_windows, timeout=5):
    """Wait for a new window to appear, up to `timeout` seconds."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_windows = get_window_addresses()
        new_windows = current_windows - existing_windows
        if new_windows:
            return new_windows.pop()
        time.sleep(0.1)  # Check every 100ms
    print("Warning: Window did not appear within timeout.")
    return None


def launch_and_manage(workspace, name, command, is_master):
    """Switch workspace, launch application, and set as master if needed."""

    print(f"Switching to workspace {workspace}")
    subprocess.run(["hyprctl", "dispatch", "workspace", f"{workspace}"], check=True)

    existing_windows = get_window_addresses()

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
    address = wait_for_window(existing_windows)
    time.sleep(0.1)
    if not address:
        logging.warning(f"No window detected for {name} in workspace {workspace}")
        return  # Skip if window did not appear

    print(f"New window detected at {address}")

    # If the window is supposed to be master and it's not already, swap it
    if is_master and not is_window_master(address, workspace):
        print(f"Swapping {address} to master in workspace {workspace}")
        subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{address}"])
        subprocess.run(["hyprctl", "dispatch", "layoutmsg", "swapwithmaster"])


def arg_parser():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="MQTT Listener for Linux")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    return args


def main():
    """Launch all applications sequentially, ensuring correct workspace assignment."""

    args = arg_parser()
    configure_logging(args)
    logging.info("Starting Hyprland Launch Apps on Login Service")

    # Initial delay - allow window manager to stabilize
    time.sleep(0.5)

    # Launch apps in order of workspace
    for workspace, apps in APPS.items():
        for app in apps:
            launch_and_manage(workspace, app["name"], app["command"], app["is_master"])

    # Switch back to default workspace in DP-2
    subprocess.run(["hyprctl", "dispatch", "workspace", "11"], check=True)
    # Move focus to master window
    master_address = get_master_window_address("11")
    if master_address:  # Check if master address exists
        subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", f"address:{master_address}"],
            check=True,
        )

    time.sleep(0.2)

    # Switch back to default workspace in DP-1
    subprocess.run(["hyprctl", "dispatch", "workspace", "1"], check=True)
    master_address = get_master_window_address("1")
    # Move focus to master window
    if master_address:  # Check if master address exists
        subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", f"address:{master_address}"],
            check=True,
        )


if __name__ == "__main__":
    main()
