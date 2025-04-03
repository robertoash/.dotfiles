#! /usr/bin/env python3

import argparse
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


def get_active_workspace_name():
    """Get the name of the currently active workspace."""
    return run_hyprctl(["activeworkspace", "-j"])["name"]


def get_windows_in_workspace(workspace_id):
    """Get window addresses in the given workspace."""
    clients = run_hyprctl(["clients", "-j"])
    return [
        client["address"]
        for client in clients
        if client["workspace"]["id"] == workspace_id
    ]


def get_windows_in_special_workspace(workspace_name):
    """Get window addresses in the specified special workspace."""
    clients = run_hyprctl(["clients", "-j"])
    return [
        client["address"]
        for client in clients
        if client["workspace"]["name"] == f"special:{workspace_name}"
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


def move_windows_to_special_workspace(window_addresses, workspace_name):
    """Move all windows to the special workspace by focusing and toggling each one."""
    for i, address in enumerate(window_addresses):
        # Focus the window
        subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{address}"])
        # Toggle it to the special workspace
        subprocess.run(["pypr", "toggle_special", workspace_name])


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Move all windows in the current workspace to another workspace "
            "or to/from a special workspace."
        )
    )
    parser.add_argument(
        "target_workspace",
        nargs="?",
        help="Target workspace ID or special workspace name (e.g., 'stash')",
    )
    args = parser.parse_args()

    # Check if we're in a special workspace
    active_workspace_name = get_active_workspace_name()
    is_special_workspace = active_workspace_name.startswith("special:")
    special_workspace_name = (
        active_workspace_name.replace("special:", "") if is_special_workspace else None
    )

    # Check if target is a special workspace
    is_special_target = args.target_workspace and not args.target_workspace.isdigit()

    if is_special_target:
        special_target_name = args.target_workspace.lower()

        if is_special_workspace and special_workspace_name == special_target_name:
            print(
                f"Already in {special_target_name} workspace. "
                f"Specify a target workspace to move from {special_target_name}."
            )
            sys.exit(1)

        # We're in a regular workspace, so move all windows to the special workspace
        active_workspace = get_active_workspace()
        window_addresses = get_windows_in_workspace(active_workspace)

        if not window_addresses:
            print(f"No windows found in workspace {active_workspace}.")
            sys.exit(0)

        # Move windows to the special workspace
        move_windows_to_special_workspace(window_addresses, special_target_name)

        print(
            f"Moved {len(window_addresses)} windows from workspace {active_workspace} "
            f"to {special_target_name}."
        )
    elif is_special_workspace and args.target_workspace:
        # We're in a special workspace, so move all windows to the target workspace
        window_addresses = get_windows_in_special_workspace(special_workspace_name)

        if not window_addresses:
            print(f"No windows found in {special_workspace_name} workspace.")
            sys.exit(0)

        # Move windows to the target workspace
        move_windows_to_workspace(window_addresses, args.target_workspace)

        print(
            f"Moved {len(window_addresses)} windows from {special_workspace_name} to "
            f"workspace {args.target_workspace}, focusing the last one."
        )
    else:
        # Regular workspace to workspace movement
        if not args.target_workspace:
            print(
                "Usage: python move_windows.py <target_workspace_id> or "
                "python move_windows.py <special_workspace_name>"
            )
            sys.exit(1)

        target_workspace = args.target_workspace
        active_workspace = get_active_workspace()

        if str(active_workspace) == target_workspace:
            print(
                "Target workspace is the same as the current workspace. No action taken."
            )
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
