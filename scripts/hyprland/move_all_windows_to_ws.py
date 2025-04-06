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


def get_active_workspace_id():
    """Get the ID of the currently active workspace."""
    return run_hyprctl(["activewindow", "-j"])["workspace"]["id"]


def get_windows_in_workspace(workspace_id):
    """Get window addresses in the given workspace."""
    clients = run_hyprctl(["clients", "-j"])
    return [
        client["address"]
        for client in clients
        if client["workspace"]["id"] == workspace_id
    ]


def get_workspace_id(workspace_name):
    """Get the workspace ID from its name."""
    workspaces = run_hyprctl(["workspaces", "-j"])
    for ws in workspaces:
        if ws["name"] == workspace_name or ws["name"] == f"special:{workspace_name}":
            return ws["id"]
    return None


def get_master_window_address(workspace_id):
    """Get the address of the master window in a workspace based on monitor orientation."""
    clients = run_hyprctl(["clients", "-j"])
    workspaces = run_hyprctl(["workspaces", "-j"])

    # Get windows in the workspace
    workspace_clients = [
        client for client in clients if client["workspace"]["id"] == workspace_id
    ]

    if not workspace_clients:
        return None

    # Get workspace info
    workspace = next((ws for ws in workspaces if ws["id"] == workspace_id), None)
    if not workspace:
        return None

    # Get monitor info
    monitors = run_hyprctl(["monitors", "-j"])
    monitor = next((m for m in monitors if m["name"] == workspace["monitor"]), None)

    if not monitor:
        # If no monitor found, just use the first window as master
        return workspace_clients[0]["address"]

    # Determine sort key based on monitor orientation
    is_vertical = monitor.get("transform", 0) in [
        1,
        3,
    ]  # 1 and 3 are vertical orientations
    sort_key = 1 if is_vertical else 0  # Use at[1] for vertical, at[0] for horizontal

    # Find the master window (lowest at[0] for horizontal, lowest at[1] for vertical)
    master_window = min(
        workspace_clients,
        key=lambda w: w.get("at", [float("inf"), float("inf")])[sort_key],
    )

    return master_window["address"]


def restore_master_window(workspace_id, target_master):
    """Restore the master window in the target workspace if needed."""
    if not target_master:
        return

    current_master = get_master_window_address(workspace_id) if workspace_id else None
    if current_master != target_master:
        # Focus the intended master
        subprocess.run(
            ["hyprctl", "dispatch", "focuswindow", f"address:{target_master}"]
        )
        # Swap it with the current master
        subprocess.run(["hyprctl", "dispatch", "layoutmsg", "swapwithmaster"])


def get_target_id(target_workspace, target_is_special):
    return (
        get_workspace_id(target_workspace)
        if target_is_special
        else int(target_workspace)
    )


def move_windows(
    window_addresses, source_id, target_id, target_workspace, target_is_special=False
):
    """Move all windows to the target workspace, handling focus based on workspace types."""

    # Get target master
    target_master = get_master_window_address(target_id) if target_id else None
    if not target_master and source_id:
        target_master = get_master_window_address(source_id)

    if target_id != source_id:
        # Move all windows
        for i, address in enumerate(window_addresses):
            if target_is_special:
                # Focus the window
                subprocess.run(
                    ["hyprctl", "dispatch", "focuswindow", f"address:{address}"]
                )
                # Toggle it to the special workspace
                subprocess.run(["pypr", "toggle_special", target_workspace])
            else:
                subprocess.run(
                    [
                        "hyprctl",
                        "dispatch",
                        "movetoworkspacesilent",
                        f"{target_workspace},address:{address}",
                    ]
                )

        # Restore master window if needed
        restore_master_window(target_id, target_master)
    else:
        print(f"Source and target workspaces are the same. No action taken.")

    return source_id, target_id, target_workspace, target_is_special


def final_focus(source_id, target_id, target_workspace, target_is_special):
    print(
        f"Final focus: {source_id}, {target_id}, {target_workspace}, {target_is_special}"
    )

    if target_id is None:
        # Recheck after move
        target_id = get_target_id(target_workspace, target_is_special)
        print(
            f"Final focus: {source_id}, {target_id}, {target_workspace}, {target_is_special}"
        )

    # Determine focus behavior based on source and target types
    source_is_special = source_id < 0
    should_focus_source = not source_is_special and target_is_special
    print(
        f"Final focus: {source_is_special}, {target_is_special}, {should_focus_source}"
    )

    commands = [
        [
            "hyprctl",
            "dispatch",
            "workspace",
            str(source_id) if should_focus_source else str(target_id),
        ],
        (
            ["hyprctl", "dispatch", "togglespecialworkspace", target_workspace]
            if should_focus_source and target_is_special
            else None
        ),
    ]

    for command in commands:
        if command:
            print(f"Issuing workspace command: {command}")
            subprocess.run(command)


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

    if not args.target_workspace:
        print(
            "Usage: python move_windows.py <target_workspace_id> or "
            "python move_windows.py <special_workspace_name>"
        )
        sys.exit(1)

    # Get current workspace info
    source_id = get_active_workspace_id()

    # Get target workspace ID
    if args.target_workspace.isdigit():
        target_id = int(args.target_workspace)
    else:
        target_id = get_target_id(args.target_workspace, True)

    # Check if source and target are the same
    if target_id is not None and source_id == target_id:
        print("Source and target workspaces are the same. No action taken.")
        sys.exit(0)

    # Get windows to move
    window_addresses = get_windows_in_workspace(source_id)
    if not window_addresses:
        print(f"No windows found in workspace {source_id}.")
        sys.exit(0)

    # Move windows
    source_id, target_id, target_workspace, target_is_special = move_windows(
        window_addresses,
        source_id,
        target_id,
        target_workspace=args.target_workspace,
        target_is_special=not args.target_workspace.isdigit(),
    )

    final_focus(source_id, target_id, target_workspace, target_is_special)

    # Print result
    print(
        f"Moved {len(window_addresses)} windows from workspace {source_id} to "
        f"{target_id}, focusing the last one."
    )


if __name__ == "__main__":
    main()
