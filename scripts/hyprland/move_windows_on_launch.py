#!/usr/bin/env python3

import json
import subprocess
import time

# Delay in seconds to wait before moving windows
DELAY = 5

# Workspace assignments for windows
# Format:
# {
#     "identifier": "title or class of window",
#     "workspace": workspace_number,
#     "make_master": True/False
# }

# workspace_assignments = [
#     {"identifier": "Zen Browser", "workspace": 11, "make_master": True},
#     {"identifier": "perplexity.ai", "workspace": 2, "make_master": False},
#     {"identifier": "chatgpt.com", "workspace": 3, "make_master": True},
#     {"identifier": "obsidian", "workspace": 4, "make_master": True},
#     {"identifier": "personal (Workspace)", "workspace": 13, "make_master": True},
#     {"identifier": "dotfiles (Workspace)", "workspace": 13, "make_master": True},
# ]

workspace_assignments = [
    {"identifier": "chatgpt.com", "workspace": 12, "make_master": False},
    {"identifier": "perplexity.ai", "workspace": 11, "make_master": False},
    {"identifier": "obsidian", "workspace": 13, "make_master": True},
    {"identifier": "dotfiles (Workspace)", "workspace": 3, "make_master": True},
    {"identifier": "personal (Workspace)", "workspace": 4, "make_master": True},
]


def get_windows():
    """Get a list of all windows from hyprctl."""
    try:
        output = subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
        return json.loads(output)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching windows: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []


def get_windows_in_workspace(workspace):
    """Get a list of all windows in a specified workspace."""
    try:
        output = subprocess.check_output(["hyprctl", "workspaces", "-j"], text=True)
        json_output = json.loads(output)
        for ws in json_output:
            if ws.get("id") == workspace:
                return int(ws.get("windows", 0))
    except subprocess.CalledProcessError as e:
        print(f"Error fetching windows in workspace {workspace}: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []


def move_window_to_workspace(window_address, workspace):
    """Move a window to a specified workspace."""
    try:
        subprocess.run(
            [
                "hyprctl",
                "dispatch",
                "movetoworkspacesilent",
                f"{workspace},address:{window_address}",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error moving window {window_address} to workspace {workspace}: {e}")


def make_window_master(window_address, workspace):
    """Make a window the master window in its workspace."""
    try:
        # Switch to the workspace to ensure the next command
        # only affects the correct workspace
        subprocess.run(["hyprctl", "dispatch", "workspace", f"{workspace}"], check=True)
        # Focus the right window
        subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", f"address:{window_address}"],
            check=True,
        )
        time.sleep(0.5)
        # Make the window the master in its new workspace
        subprocess.run(
            ["hyprctl", "dispatch", "layoutmsg", "swapwithmaster auto"], check=True
        )
    except subprocess.CalledProcessError as e:
        print(
            f"Error making window {window_address} the master in workspace {workspace}: {e}"
        )


def main():
    # Wait for a bit to let initialize and create windows
    time.sleep(DELAY)

    # Get all windows in JSON format
    windows = get_windows()

    for window in windows:
        window_address = str(window.get("address"))
        title = window.get("title", "")
        window_class = window.get("class", "")
        # Check each workspace assignment condition
        for assignment in workspace_assignments:
            if (
                assignment["identifier"] in title
                or assignment["identifier"] in window_class
            ):
                if window.get("workspace", {}).get("id") != assignment["workspace"]:
                    move_window_to_workspace(window_address, assignment["workspace"])
                if assignment["make_master"]:
                    make_window_master(window_address, assignment["workspace"])
                break  # Move to the next window after assigning the current one

    # Switch back to the first workspace on the right monitor
    subprocess.run(["hyprctl", "dispatch", "workspace", "1"], check=True)
    # Switch to the first workspace on the left monitor
    subprocess.run(["hyprctl", "dispatch", "workspace", "11"], check=True)


if __name__ == "__main__":
    main()
