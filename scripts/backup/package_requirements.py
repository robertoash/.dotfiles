#!/usr/bin/env python3

import os
import subprocess
import sys
from textwrap import dedent

SEPARATOR = "///"


def save_packages(filename, SEPARATOR="///"):
    # Get all explicitly installed packages
    all_explicit_packages = set(
        subprocess.check_output(["pacman", "-Qe"]).decode().splitlines()
    )

    # Get explicitly installed AUR packages
    aur_packages = set(
        subprocess.check_output(["pacman", "-Qme"]).decode().splitlines()
    )

    # Determine explicitly installed pacman packages by excluding AUR packages
    pacman_packages = all_explicit_packages - aur_packages

    with open(filename, "w") as f:
        # Save Pacman packages
        for package in pacman_packages:
            f.write(f"{package}{SEPARATOR}pacman\n")

        # Save AUR packages
        for package in aur_packages:
            f.write(f"{package}{SEPARATOR}yay\n")

        # Get and save Pipx packages
        pipx_packages = (
            subprocess.check_output(["pipx", "list", "--short"]).decode().splitlines()
        )
        for package in pipx_packages:
            f.write(f"{package}{SEPARATOR}pipx\n")


def reinstall_packages(filename):
    with open(filename) as f:
        for line in f:
            package, manager = line.strip().split(SEPARATOR)
            if manager == "pacman":
                subprocess.run(["sudo", "pacman", "-S", "--noconfirm", package])
            elif manager == "yay":
                subprocess.run(["yay", "-S", "--noconfirm", package])
            elif manager == "pipx":
                subprocess.run(["pipx", "install", package])


def print_help():
    help_text = dedent(
        """
        Usage:

          ./package_requirements.py -s <filename> | --save <filename>
            To save the current list of packages to a file.

          ./package_requirements.py -r <filename> | --restore <filename> | --reinstall <filename>
            To reinstall packages from a file.

          If no filename is provided, 'all_packages.txt' will be used as a file name and it
          will be saved to the path set by XDG_CONFIG_HOME. If XDG_CONFIG_HOME is not set,
          the file will be saved to '~/.config/'.

        Options:
          -s, --save        Save the current list of packages to a file.
          -r, --restore     Reinstall packages from a file (alias: --reinstall).
          --help            Show this help message and exit.
    """
    )
    print(help_text)


def is_valid_path(path):
    # Additional logic can be added here to validate path further
    return os.path.exists(path) or not os.path.isabs(path)


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--help" in args:
        print_help()
        sys.exit(1)

    action_map = {
        "-s": "save",
        "--save": "save",
        "-r": "restore",
        "--restore": "restore",
        "--reinstall": "restore",
    }
    action = None
    filename = None

    for arg in args:
        if arg.startswith("-") and len(arg) == 2 or arg in action_map:
            action = action_map.get(arg, None)
        elif is_valid_path(arg):
            filename = arg
        elif arg in action_map:
            action = action_map[arg]

    if action is None:
        print_help()
        sys.exit(1)

    if filename is None:
        filename = os.path.join(
            os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
            "all_packages.txt",
        )

    if action == "save":
        save_packages(filename)
        print(f"Packages saved to {filename}")
    elif action == "restore":
        reinstall_packages(filename)
        print(f"Packages reinstalled from {filename}")
    else:
        print("Invalid choice. Exiting.")
