#!/usr/bin/env python3

import argparse
import sys

from . import window_manager


def main(target_workspace=None):
    """
    Entry point for move_windows functionality that can be called
    with just the target_workspace parameter.
    """
    if not target_workspace:
        print("Usage: hypr-window-ops move-windows <target_ws_id|special_name>")
        return 1

    source_id = window_manager.get_active_workspace_id()
    target_is_special = not str(target_workspace).isdigit()
    target_id = window_manager.get_target_id(target_workspace, target_is_special)

    if target_id is not None and source_id == target_id:
        print("Source and target workspaces are the same. Nothing to do.")
        return 0

    window_addresses = window_manager.get_windows_in_workspace(source_id)
    if not window_addresses:
        print(f"No windows found in workspace {source_id}.")
        return 0

    result = window_manager.move_windows(
        window_addresses,
        source_id,
        target_id,
        target_workspace=target_workspace,
        target_is_special=target_is_special,
        layout=None,
    )

    if result:
        source_id, target_id, target_workspace, target_is_special = result
        window_manager.final_focus(
            source_id, target_id, target_workspace, target_is_special
        )
        print(
            f"Moved {len(window_addresses)} windows from workspace {source_id} to {target_id}."
        )

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""
Move all windows from the current workspace to a target workspace.

This utility helps you quickly organize your Hyprland desktop by allowing you to move
all windows from the current workspace to another workspace in a single command.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Move all windows to workspace 5
  python -m hypr_window_ops.move_windows 5

  # Move all windows to a special workspace
  python -m hypr_window_ops.move_windows stash
        """,
    )
    parser.add_argument(
        "target_workspace",
        nargs="?",
        help="Target workspace ID or special workspace name",
        metavar="WORKSPACE",
    )
    args = parser.parse_args()

    sys.exit(main(args.target_workspace))
