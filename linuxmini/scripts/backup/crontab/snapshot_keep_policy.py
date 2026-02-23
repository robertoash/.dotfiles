#!/usr/bin/python3

import argparse
import datetime
import logging
import os
import subprocess

from _utils import logging_utils

logging_utils.configure_logging()

# Define possible snapshot locations
LOCAL_SNAPSHOT_DIR = "/.snapshots"
EXTERNAL_SNAPSHOT_DIRS = ["/media/sda1/.snapshots", "/mnt/.snapshots"]

def process_snapshot_dir(snapshot_dir, daily_keep=3, weekly_keep=1, monthly_keep=1):
    if not os.path.exists(snapshot_dir):
        logging.warning(f"Snapshot directory does not exist: {snapshot_dir}")
        return

    logging.info(f"Processing snapshots in: {snapshot_dir}")
    policy_msg = (
        f"Policy: Keep last {daily_keep} daily, {weekly_keep} weekly, "
        f"{monthly_keep} monthly snapshots"
    )
    logging.info(policy_msg)

    # Log raw directory contents
    logging.info(f"Directory contents of {snapshot_dir}:")
    try:
        dir_contents = os.listdir(snapshot_dir)
        for i, item in enumerate(sorted(dir_contents)):
            item_path = os.path.join(snapshot_dir, item)
            item_type = "DIR" if os.path.isdir(item_path) else "FILE"
            item_size = (
                os.path.getsize(item_path) if os.path.exists(item_path) else "N/A"
            )
            logging.info(f"  [{i+1}] {item} (Type: {item_type}, Size: {item_size})")
        logging.info(f"Total items in directory: {len(dir_contents)}")
    except Exception as e:
        logging.error(f"Error listing directory contents: {e}")
        return

    # Get a list of all snapshots to process
    all_snapshots = []
    skipped_items = []

    for snapshot in dir_contents:
        try:
            if not (snapshot.startswith("backup_root_") or snapshot.startswith("backup_home_") or snapshot.startswith("backup_")):
                logging.warning(f"Skipping non-backup item: {snapshot}")
                skipped_items.append((snapshot, "Not a backup_ prefix"))
                continue

            parts = snapshot.split("_")
            if len(parts) < 3:
                logging.warning(
                    f"Skipping malformed snapshot name: {snapshot} (insufficient parts)"
                )
                skipped_items.append((snapshot, "Insufficient name parts"))
                continue

            # Handle both new format (backup_root_YYYYMMDD_HHMM, backup_home_YYYYMMDD_HHMM) 
            # and old format (backup_YYYYMMDD_HHMM)
            if snapshot.startswith("backup_root_") or snapshot.startswith("backup_home_"):
                if len(parts) < 4:
                    logging.warning(
                        f"Skipping malformed snapshot name: {snapshot} (insufficient parts for new format)"
                    )
                    skipped_items.append((snapshot, "Insufficient name parts for new format"))
                    continue
                snapshot_date_str = parts[2] + "_" + parts[3]
            else:
                # Old format: backup_YYYYMMDD_HHMM
                snapshot_date_str = parts[1] + "_" + parts[2]
            try:
                snapshot_date = datetime.datetime.strptime(
                    snapshot_date_str, "%Y%m%d_%H%M"
                )
                all_snapshots.append((snapshot_date, snapshot))
                logging.debug(
                    f"Successfully parsed snapshot: {snapshot} -> {snapshot_date}"
                )
            except ValueError as e:
                logging.warning(
                    f"Skipping snapshot with invalid date format: {snapshot}, error: {e}"
                )
                skipped_items.append((snapshot, f"Date parse error: {e}"))
        except (IndexError, ValueError) as e:
            logging.warning(f"Could not parse snapshot name: {snapshot}, error: {e}")
            skipped_items.append((snapshot, f"Parse error: {e}"))
            # Add as other with minimum date to ensure it's sorted first
            other_snapshots = [(datetime.datetime.min, snapshot)]

    # Log skipped items
    if skipped_items:
        logging.info(f"Skipped {len(skipped_items)} items:")
        for item, reason in skipped_items:
            logging.info(f"  Skipped: {item} - Reason: {reason}")

    # If no valid snapshots found, return early
    if not all_snapshots:
        logging.info(f"No valid snapshots found in {snapshot_dir}")
        return

    # Log parsed snapshots
    logging.info(f"Successfully parsed {len(all_snapshots)} snapshots:")
    for i, (date, name) in enumerate(sorted(all_snapshots)):
        logging.info(f"  [SNAPSHOT-{i+1}] {name} -> {date.strftime('%Y-%m-%d %H:%M')}")

    # Sort all snapshots by date (newest first to simplify selection logic)
    all_snapshots.sort(reverse=True)

    # Create our sets of kept snapshots
    kept_daily = []
    kept_weekly = []
    kept_monthly = []
    other_snapshots = []

    # Categorize snapshots for retention
    for date, snapshot in all_snapshots:
        # Skip already processed snapshots
        if any(s == snapshot for _, s in kept_daily + kept_weekly + kept_monthly):
            logging.debug(f"Snapshot already categorized: {snapshot}")
            continue

        # First categorize monthlies (1st of month)
        if date.day == 1 and len(kept_monthly) < monthly_keep:
            kept_monthly.append((date, snapshot))
            logging.debug(f"Categorized as monthly: {snapshot}")
        # Then weeklies (Mondays)
        elif date.weekday() == 0 and len(kept_weekly) < weekly_keep:
            kept_weekly.append((date, snapshot))
            logging.debug(f"Categorized as weekly: {snapshot}")
        # Then dailies (most recent ones)
        elif len(kept_daily) < daily_keep:
            kept_daily.append((date, snapshot))
            logging.debug(f"Categorized as daily: {snapshot}")
        # Everything else goes to other_snapshots for deletion
        else:
            other_snapshots.append((date, snapshot))
            logging.debug(f"Categorized for deletion: {snapshot}")

    # Sort snapshots by date (oldest first for display)
    kept_daily.sort()
    kept_weekly.sort()
    kept_monthly.sort()
    other_snapshots.sort()

    # Log classified snapshots
    logging.info(f"Keeping {len(kept_daily)} daily snapshots:")
    for i, (dt, name) in enumerate(kept_daily):
        logging.info(f"  [DAILY-{i+1}] {name} -> {dt.strftime('%Y-%m-%d %H:%M')}")

    logging.info(f"Keeping {len(kept_weekly)} weekly snapshots:")
    for i, (dt, name) in enumerate(kept_weekly):
        logging.info(f"  [WEEKLY-{i+1}] {name} -> {dt.strftime('%Y-%m-%d %H:%M')}")

    logging.info(f"Keeping {len(kept_monthly)} monthly snapshots:")
    for i, (dt, name) in enumerate(kept_monthly):
        logging.info(f"  [MONTHLY-{i+1}] {name} -> {dt.strftime('%Y-%m-%d %H:%M')}")

    logging.info(f"Found {len(other_snapshots)} snapshots to delete:")
    for i, (dt, name) in enumerate(other_snapshots):
        if dt == datetime.datetime.min:
            logging.info(f"  [DELETE-{i+1}] {name} -> (unknown date)")
        else:
            logging.info(f"  [DELETE-{i+1}] {name} -> {dt.strftime('%Y-%m-%d %H:%M')}")

    # Delete all snapshots in other_snapshots
    if not other_snapshots:
        logging.info("No snapshots to delete.")
    else:
        logging.info(f"Deleting {len(other_snapshots)} snapshots:")
        deletion_results = {"success": 0, "failed": 0}

        for date, snapshot in other_snapshots:
            snapshot_path = os.path.join(snapshot_dir, snapshot)
            date_str = (
                date.strftime("%Y-%m-%d %H:%M")
                if date != datetime.datetime.min
                else "(unknown date)"
            )
            logging.info(f"  Deleting: {snapshot} ({date_str})")

            # First check if the snapshot exists
            if not os.path.exists(snapshot_path):
                logging.error(f"  Cannot delete {snapshot_path}: Path does not exist")
                deletion_results["failed"] += 1
                continue

            # Check if it's actually a btrfs subvolume
            try:
                check_result = subprocess.run(
                    ["sudo", "btrfs", "subvolume", "show", snapshot_path],
                    capture_output=True,
                    text=True,
                    check=False,  # Don't raise exception here
                )

                if check_result.returncode != 0:
                    logging.warning(
                        f"  {snapshot_path} might not be a btrfs subvolume: {check_result.stderr}"
                    )

                # Try to delete anyway
                delete_result = subprocess.run(
                    ["sudo", "btrfs", "subvolume", "delete", snapshot_path],
                    capture_output=True,
                    text=True,
                    check=False,  # Don't raise exception here
                )

                if delete_result.returncode == 0:
                    logging.info(f"  Successfully deleted: {snapshot_path}")
                    deletion_results["success"] += 1
                else:
                    logging.error(
                        f"  Failed to delete {snapshot_path}: {delete_result.stderr}"
                    )
                    deletion_results["failed"] += 1

            except Exception as e:
                logging.error(f"  Error during deletion of {snapshot_path}: {str(e)}")
                deletion_results["failed"] += 1

        # Log summary of deletion results
        logging.info(
            f"Deletion summary: {deletion_results['success']} succeeded, "
            f"{deletion_results['failed']} failed"
        )


def main():
    parser = argparse.ArgumentParser(description="Manage snapshot retention policy")
    parser.add_argument(
        "--local-only", action="store_true", help="Process only local snapshots"
    )
    parser.add_argument(
        "--external-only", action="store_true", help="Process only external snapshots"
    )
    parser.add_argument(
        "--dirs", nargs="+", help="Specify custom snapshot directories to process"
    )

    args = parser.parse_args()

    if args.dirs:
        # Process custom directories
        for dir_path in args.dirs:
            process_snapshot_dir(dir_path)
    elif args.local_only:
        # Process only local snapshots
        process_snapshot_dir(LOCAL_SNAPSHOT_DIR)
    elif args.external_only:
        # Process only external snapshots (2 daily, no weekly/monthly)
        for ext_dir in EXTERNAL_SNAPSHOT_DIRS:
            process_snapshot_dir(ext_dir, daily_keep=2, weekly_keep=0, monthly_keep=0)
    else:
        # Process all: local uses full policy, external uses tighter policy
        process_snapshot_dir(LOCAL_SNAPSHOT_DIR)
        for ext_dir in EXTERNAL_SNAPSHOT_DIRS:
            process_snapshot_dir(ext_dir, daily_keep=2, weekly_keep=0, monthly_keep=0)


if __name__ == "__main__":
    main()
