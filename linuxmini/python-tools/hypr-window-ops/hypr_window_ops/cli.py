#!/usr/bin/env python3

import argparse
import sys

from . import (
    app_launcher,
    focus_location,
    monitor_movement,
    move_windows,
    snap_windows,
    stash_manager,
    switch_ws_on_monitor,
    window_properties,
)


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
  hypr-window-ops launch-apps --profile company --debug

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

  # Launch apps for company profile with debug output
  hypr-window-ops launch-apps --profile company --debug
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

    # Window property commands
    # Pin window without dimming
    pin_parser = subparsers.add_parser(
        "pin-nodim",
        help="Toggle pinning of active window without dimming",
        description="Toggle pinning of the active window without dimming.",
    )
    pin_parser.add_argument(
        "--relative-floating",
        action="store_true",
        help="Use smart targeting to find floating windows in visible workspaces",
    )
    pin_parser.add_argument(
        "--sneaky",
        action="store_true",
        help="Tag the window as 'sneaky' to make it avoid the active window",
    )

    # Toggle nofocus
    nofocus_parser = subparsers.add_parser(
        "toggle-nofocus",
        help="Toggle nofocus property for floating pinned windows",
        description="Toggle nofocus property for floating pinned windows.",
    )
    nofocus_parser.add_argument(
        "--relative-floating",
        action="store_true",
        help="Use smart targeting to find floating windows in visible workspaces",
    )
    nofocus_parser.add_argument(
        "--sneaky",
        action="store_true",
        help="Tag the window as 'sneaky' to make it avoid the active window",
    )

    # Toggle floating
    floating_parser = subparsers.add_parser(
        "toggle-floating",
        help="Toggle floating state of the active window",
        description="Toggle floating state of the active window with automatic resizing.",
    )
    floating_parser.add_argument(
        "--relative-floating",
        action="store_true",
        help="Use smart targeting to find floating windows in visible workspaces",
    )
    floating_parser.add_argument(
        "--sneaky",
        action="store_true",
        help="Tag the window as 'sneaky' to make it avoid the active window",
    )

    # Toggle fullscreen without dimming
    fullscreen_parser = subparsers.add_parser(
        "toggle-fullscreen-nodim",
        help="Toggle fullscreen without dimming for the active window",
        description="Toggle fullscreen without dimming for the active window.",
    )
    fullscreen_parser.add_argument(
        "--relative-floating",
        action="store_true",
        help="Use smart targeting to find floating windows in visible workspaces",
    )
    fullscreen_parser.add_argument(
        "--sneaky",
        action="store_true",
        help="Tag the window as 'sneaky' to make it avoid the active window",
    )

    # Toggle double size
    double_size_parser = subparsers.add_parser(
        "toggle-double-size",
        help="Toggle double size of a floating window",
        description="Toggle double size of a floating window, remembering original size.",
    )
    double_size_parser.add_argument(
        "--relative-floating",
        action="store_true",
        help="Use smart targeting to find floating windows in visible workspaces",
    )
    double_size_parser.add_argument(
        "--sneaky",
        action="store_true",
        help="Tag the window as 'sneaky' to make it avoid the active window",
    )

    # Snap window to corner
    snap_parser = subparsers.add_parser(
        "snap-to-corner",
        help="Snap window to corner",
        description="""
Snap a floating window to a specific corner or auto-detect based on cursor position.
If no corner is specified, the corner will be inferred from cursor position relative
to the window (cursor must be near a corner).
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Snap active window to lower-right corner
  hypr-window-ops snap-to-corner --corner lower-right

  # Auto-detect corner based on cursor position
  hypr-window-ops snap-to-corner

  # Snap specific window to upper-left corner
  hypr-window-ops snap-to-corner --corner upper-left --address 0x12345
        """,
    )
    snap_parser.add_argument(
        "--corner",
        choices=["lower-left", "lower-right", "upper-left", "upper-right"],
        help="Corner to snap to (if not specified, auto-detect from cursor position)",
    )
    snap_parser.add_argument(
        "--address",
        help="Window address (if not specified, use active window)",
    )
    snap_parser.add_argument(
        "--relative-floating",
        action="store_true",
        help="Use smart targeting to find floating windows in visible workspaces",
    )
    snap_parser.add_argument(
        "--sneaky",
        action="store_true",
        help="Tag the window as 'sneaky' to make it avoid the active window",
    )

    # Move window to monitor
    move_monitor_parser = subparsers.add_parser(
        "move-to-monitor",
        help="Move window to adjacent monitor with corner mirroring",
        description="""
Move a floating window to the adjacent monitor (left or right) while preserving
the relative corner position. The window's corner position will be mirrored
horizontally (e.g., lower-right becomes lower-left when moving to left monitor).
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Move active window to left monitor
  hypr-window-ops move-to-monitor --direction left

  # Move active window to right monitor with debug output
  hypr-window-ops move-to-monitor --direction right --debug
        """,
    )
    move_monitor_parser.add_argument(
        "--direction",
        choices=["left", "right"],
        required=True,
        help="Direction to move window (left or right)",
    )
    move_monitor_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output",
    )
    move_monitor_parser.add_argument(
        "--relative-floating",
        action="store_true",
        help="Use smart targeting to find floating windows in visible workspaces",
    )
    move_monitor_parser.add_argument(
        "--sneaky",
        action="store_true",
        help="Tag the window as 'sneaky' to make it avoid the active window",
    )

    # Toggle monitor stash (per-monitor toggle)
    subparsers.add_parser(
        "toggle-stash",
        help="Toggle the stash workspace for the current monitor",
        description="""
Toggle the stash workspace for the currently active monitor only.
This is a simpler alternative to toggle-stashes that only affects
the stash on the monitor you're currently using.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Toggle stash on current monitor
  hypr-window-ops toggle-stash
        """,
    )

    # Move to monitor stash
    stash_parser = subparsers.add_parser(
        "move-to-stash",
        help="Move active window to monitor's stash workspace",
        description="""
Move the active window to a stash workspace. By default, it moves to the stash
workspace bound to the current monitor (stash-left or stash-right).
You can optionally specify a specific stash to use.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Move active window to current monitor's stash
  hypr-window-ops move-to-stash

  # Move active window to a specific stash
  hypr-window-ops move-to-stash --stash stash-left
  hypr-window-ops move-to-stash --stash stash-right
        """,
    )
    stash_parser.add_argument(
        "--stash",
        help="Specific stash name to use (e.g., stash-left, stash-right)",
    )

    # Toggle sneaky tag
    sneaky_parser = subparsers.add_parser(
        "toggle-sneaky",
        help="Toggle sneaky tag on a window",
        description="Toggle the sneaky tag on a window without modifying its state.",
    )
    sneaky_parser.add_argument(
        "--relative-floating",
        action="store_true",
        help="Use smart targeting to find floating windows in visible workspaces",
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
    elif args.command == "pin-nodim":
        window_properties.pin_window_without_dimming(
            relative_floating=args.relative_floating,
            sneaky=args.sneaky,
        )
        return 0
    elif args.command == "toggle-nofocus":
        window_properties.toggle_nofocus(
            relative_floating=args.relative_floating,
            sneaky=args.sneaky,
        )
        return 0
    elif args.command == "toggle-floating":
        window_properties.toggle_floating(
            relative_floating=args.relative_floating,
            sneaky=args.sneaky,
        )
        return 0
    elif args.command == "toggle-fullscreen-nodim":
        window_properties.toggle_fullscreen_without_dimming(
            relative_floating=args.relative_floating,
            sneaky=args.sneaky,
        )
        return 0
    elif args.command == "toggle-double-size":
        window_properties.toggle_double_size(
            relative_floating=args.relative_floating,
            sneaky=args.sneaky,
        )
        return 0
    elif args.command == "snap-to-corner":
        return snap_windows.snap_window_to_corner(
            corner=args.corner,
            window_address=args.address,
            relative_floating=args.relative_floating,
            sneaky=args.sneaky,
        )
    elif args.command == "move-to-monitor":
        return monitor_movement.move_window_to_monitor(
            direction=args.direction,
            debug=args.debug,
            relative_floating=args.relative_floating,
            sneaky=args.sneaky,
        )
    elif args.command == "toggle-stash":
        return stash_manager.toggle_monitor_stash()
    elif args.command == "move-to-stash":
        return stash_manager.move_to_monitor_stash(stash_name=args.stash)
    elif args.command == "toggle-sneaky":
        window_properties.toggle_sneaky_tag(relative_floating=args.relative_floating)
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
