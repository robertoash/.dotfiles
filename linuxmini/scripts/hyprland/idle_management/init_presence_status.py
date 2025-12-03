#!/usr/bin/env python3

import glob

# Import centralized configuration
from config import (
    STATUS_FILES,
    ensure_directories,
    get_all_control_files,
    get_status_default,
)


def cleanup_stale_flags():
    """Clean up any stale exit flags from previous sessions."""

    # Updated exit flag patterns for simplified system
    exit_flag_patterns = [
        "/tmp/*_exit",
        "/tmp/*exit*",
        "/tmp/in_office_monitor_exit",
    ]

    # Get explicit cleanup files from config
    explicit_cleanup_files = get_all_control_files()

    for pattern in exit_flag_patterns:
        for flag_file in glob.glob(pattern):
            try:
                from pathlib import Path

                Path(flag_file).unlink()
                print(f"Cleaned up stale exit flag: {flag_file}")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"Warning: Could not clean up {flag_file}: {e}")

    # Explicitly clean up critical files from config
    for flag_file in explicit_cleanup_files:
        try:
            flag_file.unlink(missing_ok=True)
            print(f"Explicitly cleaned up: {flag_file}")
        except Exception as e:
            print(f"Warning: Could not clean up {flag_file}: {e}")


def init_status_files():
    """Initialize all status files needed by the simplified presence detection system."""

    # First, clean up any stale exit flags
    cleanup_stale_flags()

    # Create directories
    ensure_directories()

    # Initialize all status files with proper default values from config
    for status_name, status_file in STATUS_FILES.items():
        default_value = get_status_default(status_name)
        status_file.write_text(default_value)
        print(f"Initialized {status_file} = {default_value}")


if __name__ == "__main__":
    init_status_files()
    print("All simplified presence detection status files initialized successfully")
