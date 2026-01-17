#!/usr/bin/env python3
"""
Clean up old log files in the scripts directory.
Keeps logs from the last N days and deletes older files.
"""

import argparse
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils

logging_utils.configure_logging()

LOGS_BASE_DIR = Path("/home/rash/.config/scripts/_logs")
DEFAULT_RETENTION_DAYS = 7


def cleanup_old_logs(retention_days=DEFAULT_RETENTION_DAYS, dry_run=False):
    """Remove log files older than retention_days."""
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cutoff_timestamp = cutoff_date.timestamp()

    total_size_freed = 0
    files_deleted = 0

    logging.info(f"Cleaning up logs older than {retention_days} days (before {cutoff_date.strftime('%Y-%m-%d')})")
    if dry_run:
        logging.info("DRY RUN MODE - no files will be deleted")

    # Find all log files
    for log_file in LOGS_BASE_DIR.rglob("*.log.*"):  # Matches rotated logs with dates
        try:
            # Get file modification time
            file_mtime = log_file.stat().st_mtime

            if file_mtime < cutoff_timestamp:
                file_size = log_file.stat().st_size
                file_size_mb = file_size / (1024 * 1024)

                if dry_run:
                    logging.info(f"Would delete: {log_file.relative_to(LOGS_BASE_DIR)} ({file_size_mb:.2f} MB)")
                else:
                    log_file.unlink()
                    logging.info(f"Deleted: {log_file.relative_to(LOGS_BASE_DIR)} ({file_size_mb:.2f} MB)")

                total_size_freed += file_size
                files_deleted += 1

        except Exception as e:
            logging.error(f"Error processing {log_file}: {e}")

    size_freed_mb = total_size_freed / (1024 * 1024)
    size_freed_gb = total_size_freed / (1024 * 1024 * 1024)

    if files_deleted > 0:
        if size_freed_gb >= 1:
            logging.info(f"{'Would free' if dry_run else 'Freed'} {size_freed_gb:.2f} GB by {'deleting' if not dry_run else 'would delete'} {files_deleted} log files")
        else:
            logging.info(f"{'Would free' if dry_run else 'Freed'} {size_freed_mb:.2f} MB by {'deleting' if not dry_run else 'would delete'} {files_deleted} log files")
    else:
        logging.info("No old log files found to clean up")

    return files_deleted, total_size_freed


def main():
    parser = argparse.ArgumentParser(description="Clean up old log files")
    parser.add_argument(
        "--retention-days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Number of days to keep logs (default: {DEFAULT_RETENTION_DAYS})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )

    args = parser.parse_args()

    try:
        cleanup_old_logs(retention_days=args.retention_days, dry_run=args.dry_run)
    except Exception as e:
        logging.error(f"Failed to clean up logs: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
