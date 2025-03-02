#!/usr/bin/env python3

import json
import subprocess
import time

# Define common arguments
WAYLAND_ARGS = (
    "--new-window --enable-features=UseOzonePlatform --ozone-platform=wayland"
)
CURSOR_WORKSPACE = "/home/rash/insync/j.roberto.ash@gmail.com/Google\\ Drive/Dev_cloud/cursor/dotfiles.code-workspace"

# Define applications with name placeholders
APPS = {
    "1": [
        {
            "name": "brave_personal",
            "command": f"brave {WAYLAND_ARGS} --profile-directory='Default'",
            "is_master": True,
        },
        {
            "name": "brave_terminal",
            "command": "foot --app-id {name}",
            "is_master": False,
        },
    ],
    "2": [
        {
            "name": "brave_jobhunt",
            "command": f"brave {WAYLAND_ARGS} --profile-directory='Profile 1'",
            "is_master": True,
        },
    ],
    "3": [
        {"name": "helix", "command": "foot --app-id {name} -e hx", "is_master": True},
        {"name": "hx_terminal", "command": "foot --app-id {name}", "is_master": False},
    ],
    "4": [
        {
            "name": "cursor",
            "command": f"cursor {WAYLAND_ARGS} --file-uri {CURSOR_WORKSPACE}",
            "is_master": True,
        },
        {
            "name": "cursor_terminal",
            "command": "foot --app-id {name}",
            "is_master": False,
        },
    ],
    "11": [
        {"name": "gpt_terminal", "command": "foot --app-id {name}", "is_master": True},
        {
            "name": "gpt_zen",
            "command": f"brave {WAYLAND_ARGS} --profile-directory='AppProfile' --app=https://chatgpt.com/",
            "is_master": False,
        },
    ],
    "12": [
        {
            "name": "obsidian",
            "command": "OBSIDIAN_USE_WAYLAND=1 obsidian -enable-features=UseOzonePlatform -ozone-platform=wayland",
            "is_master": True,
        },
        {
            "name": "obsidian_terminal",
            "command": "foot --app-id {name}",
            "is_master": False,
        },
    ],
    "13": [
        {
            "name": "perplexity_terminal",
            "command": "foot --app-id {name}",
            "is_master": True,
        },
        {
            "name": "perplexity_zen",
            "command": f"brave {WAYLAND_ARGS} --profile-directory='AppProfile' --app=https://perplexity.ai",
            "is_master": False,
        },
    ],
}


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

        return master_window.get("address") == window_address

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

    # Replace `{name}` with the actual name
    command = command.format(name=name)

    print(f"Launching: {command}")
    subprocess.Popen(command, shell=True)

    # Wait specifically for this window
    address = wait_for_window(existing_windows)
    if not address:
        return  # Skip if window did not appear

    print(f"New window detected at {address}")

    # If the window is supposed to be master and it's not already, swap it
    if is_master and not is_window_master(address, workspace):
        print(f"Swapping {address} to master in workspace {workspace}")
        subprocess.run(
            ["hyprctl", "dispatch", "layoutmsg", "swapwithmaster", f"address:{address}"]
        )


def main():
    """Launch all applications sequentially, ensuring correct workspace assignment."""
    for workspace, apps in APPS.items():
        for app in apps:
            launch_and_manage(workspace, app["name"], app["command"], app["is_master"])

    # Switch back to default workspaces
    subprocess.run(["hyprctl", "dispatch", "workspace", "1"], check=True)
    subprocess.run(["hyprctl", "dispatch", "workspace", "11"], check=True)


if __name__ == "__main__":
    main()
