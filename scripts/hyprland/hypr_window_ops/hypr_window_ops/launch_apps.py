#!/usr/bin/env python3

import argparse
import sys

from . import app_launcher, config


def main():
    """CLI entry point for launching apps directly."""
    parser = argparse.ArgumentParser(
        description="""
Launch applications defined in the configuration based on a profile.

This utility starts applications in their designated workspaces with
proper window placement and master/slave configuration according to
the profile configuration.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch apps for the default profile
  python -m hypr_window_ops.launch_apps

  # Launch apps for job hunting with debug output
  python -m hypr_window_ops.launch_apps --profile jobhunt --debug
        """,
    )
    parser.add_argument(
        "--profile",
        default=config.DEFAULT_PROFILE,
        help="Profile to launch (default: %(default)s)",
        metavar="PROFILE",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable detailed debug logging"
    )
    args = parser.parse_args()

    return app_launcher.launch_profile_apps(args.profile, args.debug)


if __name__ == "__main__":
    sys.exit(main())
