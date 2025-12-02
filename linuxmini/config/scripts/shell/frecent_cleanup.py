#!/usr/bin/env python3
"""
Frecent Cleanup Script

Removes non-existent files from the fre database.
Can be run manually or via cronjob for automated cleanup.

Note: Zoxide automatically removes non-existent directories, so no cleanup needed.
"""

import argparse
import logging
import os
import subprocess
import sys

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

# Parse command-line arguments
parser = argparse.ArgumentParser(
    description="Clean up non-existent files from fre database."
)
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

# Configure logging
logging_utils.configure_logging()
if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.ERROR)


def run_command(cmd):
    """Run a shell command and return its output."""
    try:
        logging.debug(f"Running command: {cmd}")
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running command '{cmd}': {e}")
        print(f"Error running command '{cmd}': {e}", file=sys.stderr)
        return None


def cleanup_frecent():
    """Clean up non-existent files from fre database."""
    logging.debug("Starting fre database cleanup")
    print("🧹 Cleaning up non-existent files from fre database...")

    # Check if fre command exists
    if subprocess.run(["which", "fre"], capture_output=True).returncode != 0:
        logging.error("fre command not found")
        print("❌ Error: fre command not found", file=sys.stderr)
        return False

    # Get all files from fre database
    files_output = run_command("fre --sorted")
    if files_output is None:
        logging.error("Could not get files from fre database")
        print("❌ Error: Could not get files from fre database", file=sys.stderr)
        return False

    if not files_output:
        logging.debug("No files in fre database to check")
        print("✅ No files in fre database to check.")
        return True

    files = files_output.split("\n")
    removed_count = 0

    for file_path in files:
        if not file_path.strip():
            continue

        logging.debug(f"Checking file: {file_path}")

        # Check if file exists
        if not os.path.isfile(file_path):
            logging.debug(f"File does not exist, removing: {file_path}")
            # Remove from fre database
            if run_command(f"fre --delete '{file_path}'") is not None:
                print(f"🗑️  Removed: {file_path}")
                removed_count += 1
            else:
                logging.error(f"Failed to remove: {file_path}")
                print(f"⚠️  Failed to remove: {file_path}", file=sys.stderr)

    logging.debug(f"Cleanup complete. Removed {removed_count} files")
    print(f"✅ Cleanup complete. Removed {removed_count} non-existent files.")

    # Note about zoxide
    print("ℹ️  Note: Zoxide automatically removes non-existent directories.")

    return True


def main():
    """Main function."""
    try:
        logging.debug("Starting frecent cleanup script")
        success = cleanup_frecent()
        logging.debug(f"Cleanup finished with success: {success}")
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logging.debug("Cleanup interrupted by user")
        print("\n❌ Cleanup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
