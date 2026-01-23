#!/usr/bin/env python3

import os
import subprocess
import sys
from textwrap import dedent

SEPARATOR = "###"

MANAGERS = {
    "pacman": {
        "retrieve": ["sh", "-c", "pacman -Qen"],
        "parse": lambda line: line.strip().split(maxsplit=1),
        "restore": lambda pkg, ver=None: ["sudo", "pacman", "-S", "--noconfirm", pkg],
    },
    "paru": {
        "retrieve": ["sh", "-c", "pacman -Qem"],
        "parse": lambda line: line.strip().split(maxsplit=1),
        "restore": lambda pkg, ver=None: ["paru", "-S", "--noconfirm", pkg],
    },
    "cargo": {
        "retrieve": [
            "sh",
            "-c",
            "cargo install --list | grep -E '^[^ ]+ v[0-9]'",
        ],
        "parse": lambda line: (
            line.split()[0],
            line.split()[1][:-1] if len(line.split()) > 1 else None,
        ),
        "restore": lambda pkg, ver=None: ["cargo", "install", pkg],
    },
    "uv": {
        "retrieve": ["uv", "tool", "list"],
        "parse": lambda line: (
            line.strip().split(maxsplit=1)
            if line.strip() and not line.startswith("-") and " v" in line
            else None  # Return None instead of (None, None)
        ),
        "restore": lambda pkg, ver=None: ["uv", "tool", "install", pkg],
    },
    "ya": {
        "retrieve": [
            "sh",
            "-c",
            "ya pkg list | grep / | "
            "awk '{match($0, /^[[:space:]]*([^(]+)[[:space:]]*\\(([^)]+)\\)/, arr); "
            "print arr[1] \" \" arr[2]}' | awk '{$1=$1};1'",
        ],
        "parse": lambda line: line.strip().split(maxsplit=1),
        "restore": lambda pkg, ver=None: ["ya", "pkg", "add", pkg],
    },
    "fisher": {
        "retrieve": [
            "fish",
            "-c",
            "fisher list",
        ],
        "parse": lambda line: (line.strip(), None),
        "restore": lambda pkg, ver=None: ["fisher", "install", pkg],
    },
    "npm": {
        "retrieve": ["sh", "-c", "unset NPM_CONFIG_PREFIX && npm list -g --depth=0 | grep '@'"],
        "parse": lambda line: line.strip()[4:].rsplit("@", 1),
        "restore": lambda pkg, ver=None: ["npm", "install", "-g", pkg],
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
                    parsed = commands["parse"](package)
                    if parsed is not None and parsed[0] is not None:
                        name, version = parsed
                        version = version or ""
                        f.write(f"{name}{SEPARATOR}{version}{SEPARATOR}{manager}\n")
            except subprocess.CalledProcessError:
                print(f"Warning: Failed to retrieve packages for {manager}")


def reinstall_packages(filename):
    with open(filename) as f:
        for line in f:
            parts = line.strip().split(SEPARATOR)
            if len(parts) != 3:
                print(f"Warning: Invalid line in {filename}: {line.strip()}")
                continue
            package, version, manager = parts
            if manager in MANAGERS:
                result = subprocess.run(MANAGERS[manager]["restore"](package, version))
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
        hostname = os.uname().nodename
        filename = os.path.expanduser(f"~/.dotfiles/{hostname}/config/all_packages.txt")

    if action == "save":
        save_packages(filename)
        print(f"Packages saved to {filename}")
    elif action == "restore":
        reinstall_packages(filename)
        print(f"Packages reinstalled from {filename}")
    else:
        print("Invalid choice. Exiting.")
