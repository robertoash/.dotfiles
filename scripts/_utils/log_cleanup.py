#!/usr/bin/env python3

import datetime
import os
import re
import sys
from pathlib import Path

DAYS_THRESHOLD = 5


def is_old_logfile(file_path, days_threshold=DAYS_THRESHOLD):
    """
    Determine if a log file is older than the specified threshold.
    Handles both timestamp-based filenames and modification time checks.
    """
    now = datetime.datetime.now()

    # Check if the file has a date in its name (e.g. filename.log.YYYY-MM-DD)
    date_match = re.search(r"\.(\d{4}-\d{2}-\d{2})$", file_path.name)
    if date_match:
        try:
            file_date = datetime.datetime.strptime(date_match.group(1), "%Y-%m-%d")
            days_diff = (now - file_date).days
            return days_diff > days_threshold
        except ValueError:
            # If date parsing fails, fall back to file modification time
            pass

    # If no date in filename or date parsing failed, use file modification time
    file_stat = file_path.stat()
    mod_time = datetime.datetime.fromtimestamp(file_stat.st_mtime)
    days_diff = (now - mod_time).days

    return days_diff > days_threshold


def cleanup_logs(log_dir, days_threshold=DAYS_THRESHOLD, dry_run=False):
    """
    Recursively traverse the log directory and remove files older than the specified threshold.

    Args:
        log_dir: Path to the log directory
        days_threshold: Number of days to keep logs (default: 5)
        dry_run: If True, only print actions without performing them
    """
    log_dir = Path(log_dir).expanduser().resolve()

    if not log_dir.exists() or not log_dir.is_dir():
        print(f"Error: {log_dir} does not exist or is not a directory")
        return False

    deleted_count = 0
    error_count = 0

    # Walk through directory tree
    for root, dirs, files in os.walk(log_dir):
        root_path = Path(root)

        # Process files in current directory
        for file in files:
            file_path = root_path / file

            # Process log files (ends with .log or has .log. in the name)
            if file.endswith(".log") or ".log." in file:
                # Check if file is older than threshold
                if is_old_logfile(file_path, days_threshold):
                    if dry_run:
                        print(f"Would delete: {file_path}")
                        deleted_count += 1
                    else:
                        try:
                            file_path.unlink()
                            print(f"Deleted: {file_path}")
                            deleted_count += 1
                        except Exception as e:
                            print(f"Error deleting {file_path}: {e}")
                            error_count += 1

    action = "Would delete" if dry_run else "Deleted"
    print(f"\n{action} {deleted_count} log files")
    if error_count > 0:
        print(f"Encountered {error_count} errors")

    return deleted_count > 0 and error_count == 0


def main():
    # Define log directory
    log_dir = Path.home() / ".config" / "scripts" / "_logs"

    # Parse command line arguments
    dry_run = "--dry-run" in sys.argv
    days = DAYS_THRESHOLD

    for arg in sys.argv:
        if arg.startswith("--days="):
            try:
                days = int(arg.split("=")[1])
            except (ValueError, IndexError):
                print(f"Invalid days argument: {arg}")
                days = DAYS_THRESHOLD

    print(f"Cleaning log files older than {days} days from {log_dir}")
    if dry_run:
        print("Dry run mode: no files will be deleted")

    cleanup_logs(log_dir, days, dry_run)


if __name__ == "__main__":
    main()
