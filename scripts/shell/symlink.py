#!/usr/bin/env python3
import argparse
import glob
import os
import readline
import shutil
import sys


def complete_path(text, state):
    # Expand ~ to home directory
    text = os.path.expanduser(text)
    # Use glob to match files/folders
    results = glob.glob(text + "*")
    # Add a trailing slash to directories
    results = [r + "/" if os.path.isdir(r) else r for r in results]
    # Remove the expanded home directory for display if the user typed ~
    if text.startswith(os.path.expanduser("~")):
        results = [
            (
                "~" + r[len(os.path.expanduser("~")) :]
                if r.startswith(os.path.expanduser("~"))
                else r
            )
            for r in results
        ]
    try:
        return results[state]
    except IndexError:
        return None


readline.set_completer_delims(" \t\n;")
readline.set_completer(complete_path)
readline.parse_and_bind("tab: complete")


def prompt(message):
    try:
        return input(message).strip()
    except EOFError:
        print("\nAborted.")
        sys.exit(1)


def get_paths():
    parser = argparse.ArgumentParser(
        description="Create a symlink (safe and human-friendly).",
        usage="symlink --link_path=/path/to/link --link_target_path=/path/to/real/thing",
    )
    parser.add_argument("--link_path", type=str, help="Where to create the symlink")
    parser.add_argument(
        "--link_target_path", type=str, help="The real file or folder to point to"
    )

    args, extra = parser.parse_known_args()

    if extra:
        parser.error(
            "Positional arguments are not allowed. Use --link_path and --link_target_path."
        )

    if args.link_path and args.link_target_path:
        return args.link_path, args.link_target_path

    print("\n🔧 Interactive Mode:\n")
    link_path = prompt("Enter the **symlink path** to create (e.g., /usr/bin/mytool): ")
    link_target_path = prompt(
        "Enter the **real file or folder** to point to (e.g., ~/.config/scripts/tool.py): "
    )
    return link_path, link_target_path


def confirm(message):
    choice = input(f"{message} [y/N]: ").strip().lower()
    return choice == "y"


def main():
    link_path, link_target_path = get_paths()
    link_path = os.path.expanduser(link_path)
    link_target_path = os.path.expanduser(link_target_path)

    print("\n🚀 Preparing to create symlink:\n")
    print(f"    {link_path}  -->  {link_target_path}\n")

    if not os.path.exists(link_target_path):
        print(f"❌ Error: The real destination '{link_target_path}' does not exist.")
        sys.exit(1)

    if os.path.lexists(link_path):
        print(f"⚠️ Warning: Symlink path '{link_path}' already exists.")
        if not confirm("   Overwrite it?"):
            print("Aborted. 👋")
            sys.exit(0)
        try:
            if os.path.islink(link_path) or os.path.isfile(link_path):
                os.unlink(link_path)
            elif os.path.isdir(link_path):
                shutil.rmtree(link_path)
        except Exception as e:
            print(f"❌ Failed to remove existing symlink path: {e}")
            sys.exit(1)

    try:
        os.symlink(link_target_path, link_path)
        print(f"✅ Success! Created symlink:\n   {link_path} -> {link_target_path}")
    except Exception as e:
        print(f"❌ Failed to create symlink: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user. Goodbye! 👋")
        sys.exit(130)
