#!/usr/bin/env python3

import argparse
import sys

from . import app_launcher, focus_location, move_windows, switch_ws_on_monitor


def main():
    """Main entry point for the hypr_window_ops CLI."""
    parser = argparse.ArgumentParser(
        description="""
Hyprland Window Operations Toolset

A collection of utilities for managing windows and workspaces in Hyprland.
This tool helps you efficiently organize your workspace by moving windows
and launching applications in a controlled manner.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog="hypr-window-ops",
        epilog="""
Examples:
  # Move all windows from current workspace to workspace 2
  hypr-window-ops move-windows 2

  # Move all windows to a special workspace
  hypr-window-ops move-windows stash

  # Launch apps for the default profile
  hypr-window-ops launch-apps

  # Launch apps for a specific profile with debug logging
  hypr-window-ops launch-apps --profile jobhunt --debug

  # Focus window at specific location (master) on left monitor
  hypr-window-ops focus_location left master
        """,
    )
    subparsers = parser.add_subparsers(
        dest="command",
        title="available commands",
        description="Use one of the following commands:",
        help="Command to run",
    )

    # Move windows subcommand
    move_parser = subparsers.add_parser(
        "move-windows",
        help="Move all windows from current workspace to another",
        description="""
Move all windows from the current workspace to a target workspace.
This is useful for quickly organizing your desktop or temporarily
stashing windows in a special workspace.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Move to a numbered workspace
  hypr-window-ops move-windows 5

  # Move to a special workspace
  hypr-window-ops move-windows stash
        """,
    )
    move_parser.add_argument(
        "target_workspace",
        nargs="?",
        help="Target workspace ID or special workspace name",
        metavar="WORKSPACE",
    )

    # Launch apps subcommand
    launch_parser = subparsers.add_parser(
        "launch-apps",
        help="Launch applications based on profile",
        description="""
Launch applications defined in the configuration file based on a profile.
Applications will be launched in their designated workspaces with
proper window placement and master/slave configuration.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch apps for the default profile
  hypr-window-ops launch-apps

  # Launch apps for job hunting with debug output
  hypr-window-ops launch-apps --profile jobhunt --debug
        """,
    )
    launch_parser.add_argument(
        "--profile",
        default="personal",
        help="Profile to launch (default: %(default)s)",
        metavar="PROFILE",
    )
    launch_parser.add_argument(
        "--debug", action="store_true", help="Enable detailed debug logging"
    )

    # Focus location subcommand
    focus_parser = subparsers.add_parser(
        "focus_location",
        help="Focus window at a specific location on monitor",
        description="""
Focus a window at a specific location (master, slave1, etc.) on a monitor.
This helps with quickly navigating between window positions in Hyprland.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Focus the master window on the left monitor
  hypr-window-ops focus_location left master

  # Focus the second slave window on the right monitor
  hypr-window-ops focus_location right slave2
        """,
    )
    focus_parser.add_argument(
        "monitor_side",
        choices=["left", "right"],
        help="Which monitor to target (left or right)",
    )
    focus_parser.add_argument(
        "position",
        choices=["master", "slave1", "slave2", "slave3"],
        help="Window position to focus (master, slave1, slave2, slave3)",
    )

    # Switch workspace on monitor subcommand
    switch_ws_parser = subparsers.add_parser(
        "switch-ws",
        help="Switch to the Nth workspace on the current monitor",
        description="""
Switch to the Nth workspace (by order) on the currently focused monitor.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  hypr-window-ops switch-ws 1
  hypr-window-ops switch-ws 2
        """,
    )
    switch_ws_parser.add_argument(
        "n",
        help=(
            "Workspace number (1 = first on monitor, 2 = second, etc.) "
            "or 'next' for next available"
        ),
        metavar="N|next",
    )

    # Parse arguments
    args = parser.parse_args()

    # Handle commands
    if args.command == "move-windows":
        if not args.target_workspace:
            print("Error: target_workspace is required.")
            move_parser.print_help()
            return 1
        return move_windows.main(args.target_workspace)
    elif args.command == "launch-apps":
        return app_launcher.launch_profile_apps(
            profile_name=args.profile, debug=args.debug
        )
    elif args.command == "focus_location":
        return focus_location.focus_by_location(args.monitor_side, args.position)
    elif args.command == "switch-ws":
        if args.n == "next":
            return switch_ws_on_monitor.switch_to_next_workspace_on_focused_monitor()
        try:
            n = int(args.n)
        except ValueError:
            print("Argument must be an integer or 'next'.")
            return 1
        return switch_ws_on_monitor.switch_to_nth_workspace_on_focused_monitor(n)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
