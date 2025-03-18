#! /usr/bin/env python3

import json
import subprocess
import sys


def run_hyprctl(command):
    """Run a hyprctl command and return the parsed JSON output."""
    result = subprocess.run(["hyprctl"] + command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {' '.join(command)}: {result.stderr}")
        sys.exit(1)
    return json.loads(result.stdout)


def get_active_workspace():
    """Get the ID of the currently active workspace."""
    return run_hyprctl(["activeworkspace", "-j"])["id"]


def get_windows_in_workspace(workspace_id):
    """Get window addresses in the given workspace."""
    clients = run_hyprctl(["clients", "-j"])
    return [
        client["address"]
        for client in clients
        if client["workspace"]["id"] == workspace_id
    ]


def move_windows_to_workspace(window_addresses, target_workspace):
    """Move all windows to the target workspace, making the last one move with focus."""
    for i, address in enumerate(window_addresses):
        command = (
            "movetoworkspace"
            if i == len(window_addresses) - 1
            else "movetoworkspacesilent"
        )
        subprocess.run(
            ["hyprctl", "dispatch", command, f"{target_workspace},address:{address}"]
        )


def main():
    if len(sys.argv) != 2:
        print("Usage: python move_windows.py <target_workspace_id>")
        sys.exit(1)

    target_workspace = sys.argv[1]
    active_workspace = get_active_workspace()

    if str(active_workspace) == target_workspace:
        print("Target workspace is the same as the current workspace. No action taken.")
        sys.exit(0)

    window_addresses = get_windows_in_workspace(active_workspace)

    if not window_addresses:
        print(f"No windows found in workspace {active_workspace}.")
        sys.exit(0)

    move_windows_to_workspace(window_addresses, target_workspace)

    print(
        f"Moved {len(window_addresses)} windows from workspace {active_workspace} to "
        f"{target_workspace}, focusing the last one."
    )


if __name__ == "__main__":
    main()
