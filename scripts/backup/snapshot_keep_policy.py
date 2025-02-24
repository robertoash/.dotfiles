#!/usr/bin/env python3

import datetime
import logging
import os
import subprocess

from _utils import logging_utils

logging_utils.configure_logging()

snapshot_dir = "/home/rash/.local/.snapshots"
daily_keep = 6
weekly_keep = 3
monthly_keep = 1

# Get current date
today = datetime.datetime.now()
weekday = today.weekday()
day_of_month = today.day

# Classify snapshots
daily_snapshots = []
weekly_snapshots = []
monthly_snapshots = []


for snapshot in os.listdir(snapshot_dir):
    snapshot_date_str = snapshot.split("_")[1] + "_" + snapshot.split("_")[2]
    snapshot_date = datetime.datetime.strptime(snapshot_date_str, "%Y%m%d_%H%M")

    if snapshot_date.day == 1:
        monthly_snapshots.append((snapshot_date, snapshot))
    elif snapshot_date.weekday() == 0:
        weekly_snapshots.append((snapshot_date, snapshot))
    else:
        daily_snapshots.append((snapshot_date, snapshot))

# Sort snapshots by date
daily_snapshots.sort()
weekly_snapshots.sort()
monthly_snapshots.sort()

# Determine snapshots to delete
snapshots_to_delete = []

if len(daily_snapshots) > daily_keep:
    snapshots_to_delete.extend(daily_snapshots[:-daily_keep])
if len(weekly_snapshots) > weekly_keep:
    snapshots_to_delete.extend(weekly_snapshots[:-weekly_keep])
if len(monthly_snapshots) > monthly_keep:
    snapshots_to_delete.extend(monthly_snapshots[:-monthly_keep])

# Delete old snapshots
if not snapshots_to_delete:
    logging.info("No snapshots to delete.")
else:
    for _, snapshot in snapshots_to_delete:
        snapshot_path = os.path.join(snapshot_dir, snapshot)
        subprocess.run(
            ["sudo", "btrfs", "subvolume", "delete", snapshot_path], check=True
        )
        logging.info(f"Deleted snapshot: {snapshot_path}")
