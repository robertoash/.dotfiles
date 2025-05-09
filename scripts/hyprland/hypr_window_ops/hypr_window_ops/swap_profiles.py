#!/usr/bin/env python3

import argparse

from . import profile_manager


def main_with_args(args):
    """Entry point that can be called with args directly."""
    profile_manager.swap_to_profile(args.to)
    return 0


def main():
    """Original CLI entry point."""
    parser = argparse.ArgumentParser(
        description="""
Swap between saved window layouts and configurations.

This utility allows you to quickly switch between different workspace profiles,
saving your current window layout before switching. This is useful for switching
contexts between different tasks, such as personal use and job hunting.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Switch to personal profile
  python -m hypr_window_ops.swap_profiles --to personal

  # Switch to job hunting profile
  python -m hypr_window_ops.swap_profiles --to jobhunt
        """,
    )
    parser.add_argument(
        "--to",
        choices=["personal", "jobhunt"],
        required=True,
        help="Profile to switch to (personal or jobhunt)",
        metavar="PROFILE",
    )
    args = parser.parse_args()

    return main_with_args(args)


if __name__ == "__main__":
    import sys

    sys.exit(main())
