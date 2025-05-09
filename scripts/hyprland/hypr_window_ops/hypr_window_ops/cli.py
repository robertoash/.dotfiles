#!/usr/bin/env python3

import argparse
import sys

from . import app_launcher, move_windows


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
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
