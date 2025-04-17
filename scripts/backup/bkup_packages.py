#!/usr/bin/env python3

import os
import subprocess
import sys
from textwrap import dedent

SEPARATOR = "###"

MANAGERS = {
    "pacman": {
        "retrieve": ["sh", "-c", "pacman -Qe | awk '{print $1}'"],
        "restore": lambda pkg: ["sudo", "pacman", "-S", "--noconfirm", pkg],
    },
    "yay": {
        "retrieve": ["sh", "-c", "pacman -Qme | awk '{print $1}'"],
        "restore": lambda pkg: ["yay", "-S", "--noconfirm", pkg],
    },
    "pipx": {
        "retrieve": ["sh", "-c", "pipx list --short | awk '{print $1}'"],
        "restore": lambda pkg: ["pipx", "install", pkg],
    },
    "flatpak": {
        "retrieve": ["sh", "-c", "flatpak list --app --columns=application"],
        "restore": lambda pkg: ["flatpak", "install", "--noninteractive", pkg],
    },
    "ya": {
        "retrieve": [
            "sh",
            "-c",
            "ya pack -l | grep / | awk '{gsub(/\\s+\\([^)]+\\)/,\"\"); print}' | awk '{$1=$1};1'",
        ],
        "restore": lambda pkg: ["ya", "pack", "install", pkg],
    },
}


def save_packages(filename):
    with open(filename, "w") as f:
        for manager, commands in MANAGERS.items():
            try:
                packages = (
                    subprocess.check_output(commands["retrieve"]).decode().splitlines()
                )
                for package in packages:
                    f.write(f"{package}{SEPARATOR}{manager}\n")
            except subprocess.CalledProcessError:
                print(f"Warning: Failed to retrieve packages for {manager}")


def reinstall_packages(filename):
    with open(filename) as f:
        for line in f:
            parts = line.strip().split(SEPARATOR)
            if len(parts) != 2:
                print(f"Warning: Invalid line in {filename}: {line.strip()}")
                continue
            package, manager = parts
            if manager in MANAGERS:
                result = subprocess.run(MANAGERS[manager]["restore"](package))
                if result.returncode != 0:
                    print(f"Failed to install {package} via {manager}")


def print_help():
    help_text = dedent(
        """
        Usage:

          ./package_requirements.py -s|--save <filename>
            To save the current list of packages to a file.

          ./package_requirements.py -r|--restore|--reinstall <filename>
            To reinstall packages from a file.

          If no filename is provided, 'all_packages.txt' will be used as a file name
          and it will be saved to the path set by XDG_CONFIG_HOME. If XDG_CONFIG_HOME
          is not set, the file will be saved to '~/.config/'.

          If the --reinstall flag is used, the packages will be reinstalled from
          the contents of the file.

        Options:
          -s, --save        Save the current list of packages to a file.
          -r, --restore     Reinstall packages from a file (alias: --reinstall).
          --help            Show this help message and exit.
        """
    )
    print(help_text)


def is_valid_path(path):
    return os.path.exists(os.path.expanduser(path)) or not os.path.isabs(path)


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print_help()
        sys.exit(1)

    action_map = {
        "-s": "save",
        "--save": "save",
        "-r": "restore",
        "--restore": "restore",
        "--reinstall": "restore",
    }
    action, filename = None, None

    for i, arg in enumerate(args):
        if arg in action_map:
            action = action_map[arg]
            if i + 1 < len(args) and not args[i + 1].startswith("-"):
                filename = args[i + 1]
        elif is_valid_path(arg):
            filename = arg

    if action is None:
        action = "save"

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
