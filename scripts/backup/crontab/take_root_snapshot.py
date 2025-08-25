#!/usr/bin/python3

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path

from _utils import logging_utils

logging_utils.configure_logging()

# Define the locations
home_dir = Path("/home/rash/")
local_snapshot_dir = Path("/.snapshots")
external_drive_dir = Path("/mnt/.snapshots")


def create_snapshot(snapshot_name):
    try:
        # Create a read-only local snapshot
        subprocess.run(
            [
                "sudo",
                "btrfs",
                "subvolume",
                "snapshot",
                "-r",
                "/",
                str(local_snapshot_dir.joinpath(snapshot_name)),
            ],
            check=True,
        )
        logging.info(
            f"Snapshot {snapshot_name} created successfully in {local_snapshot_dir}"
        )
        print(f"Snapshot {snapshot_name} created successfully in {local_snapshot_dir}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error creating snapshot: {e}")
        print(f"Error creating snapshot: {e}", file=sys.stderr)
        sys.exit(1)


def get_snapshot_size(snapshot_path):
    """Get the size of a btrfs snapshot in bytes"""
    try:
        result = subprocess.run([
            "sudo", "btrfs", "filesystem", "du", "-s", str(snapshot_path)
        ], capture_output=True, text=True, check=True)
        
        # Parse output: "     Total   Exclusive  Set shared  Filename"
        # We want the "Total" column which is the first number
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if str(snapshot_path) in line:
                parts = line.split()
                if len(parts) >= 1:
                    size_str = parts[0]
                    # Convert size string to bytes (handles K, M, G suffixes)
                    multipliers = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
                    if size_str[-1] in multipliers:
                        return int(float(size_str[:-1]) * multipliers[size_str[-1]])
                    else:
                        return int(size_str)
        return 0
    except (subprocess.CalledProcessError, ValueError, IndexError) as e:
        logging.warning(f"Could not determine size of {snapshot_path}: {e}")
        return 0


def cleanup_old_snapshots_for_size(required_bytes):
    """Remove oldest snapshots to make space for a snapshot of the given size"""
    try:
        # Get current free space
        usage = shutil.disk_usage(external_drive_dir)
        available_bytes = usage.free
        
        # Add 1GB buffer for safety
        buffer_bytes = 1024 * 1024 * 1024
        needed_bytes = required_bytes + buffer_bytes
        
        if available_bytes >= needed_bytes:
            logging.info(f"Sufficient space available ({available_bytes // (1024**3):.1f}GB free, {needed_bytes // (1024**3):.1f}GB needed)")
            return
        
        space_to_free = needed_bytes - available_bytes
        logging.info(f"Need to free {space_to_free // (1024**3):.1f}GB for new snapshot")
        
        # Get all snapshots sorted by modification time (oldest first)
        snapshots = []
        if external_drive_dir.exists():
            for item in external_drive_dir.iterdir():
                if item.is_dir() and (item.name.startswith('backup_home_') or item.name.startswith('backup_root_')):
                    snapshots.append(item)
        
        # Sort by modification time (oldest first)
        snapshots.sort(key=lambda x: x.stat().st_mtime)
        
        # Remove oldest snapshots until we have enough space
        freed_bytes = 0
        removed_count = 0
        
        while snapshots and freed_bytes < space_to_free:
            oldest = snapshots.pop(0)
            try:
                # Get size before deletion
                snapshot_size = get_snapshot_size(oldest)
                
                subprocess.run([
                    "sudo", "btrfs", "subvolume", "delete", str(oldest)
                ], check=True, capture_output=True, text=True)
                
                freed_bytes += snapshot_size
                removed_count += 1
                logging.info(f"Removed old snapshot: {oldest.name} ({snapshot_size // (1024**3):.1f}GB)")
                
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to remove snapshot {oldest.name}: {e}")
                break
        
        if removed_count > 0:
            logging.info(f"Cleaned up {removed_count} old snapshots, freed {freed_bytes // (1024**3):.1f}GB")
            print(f"Cleaned up {removed_count} old snapshots, freed {freed_bytes // (1024**3):.1f}GB")
    
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
        print(f"Warning: Cleanup failed: {e}", file=sys.stderr)


def send_snapshot(snapshot_name):
    # Ensure the snapshot directory exists and is a Btrfs filesystem
    if (
        not local_snapshot_dir.joinpath(snapshot_name).is_dir()
        or not local_snapshot_dir.joinpath(snapshot_name).exists()
    ):
        logging.error(
            f"Snapshot directory {local_snapshot_dir}/{snapshot_name} does not exist."
        )
        print(
            f"Snapshot directory {local_snapshot_dir}/{snapshot_name} does not exist."
        )
        return

    # Calculate size of snapshot we're about to send and cleanup if needed
    snapshot_size = get_snapshot_size(local_snapshot_dir.joinpath(snapshot_name))
    cleanup_old_snapshots_for_size(snapshot_size)

    send_command = [
        "sudo",
        "btrfs",
        "send",
        str(local_snapshot_dir.joinpath(snapshot_name)),
    ]
    receive_command = ["sudo", "btrfs", "receive", external_drive_dir]

    try:
        # Open a subprocess for 'btrfs send'
        with subprocess.Popen(send_command, stdout=subprocess.PIPE) as send_proc:
            if send_proc.stdout is not None:
                # Use the output of 'btrfs send' as input for 'btrfs receive'
                subprocess.run(receive_command, stdin=send_proc.stdout, check=True)
                
                # Make the received snapshot read-only
                subprocess.run([
                    "sudo", "btrfs", "property", "set", "-ts", 
                    str(external_drive_dir.joinpath(snapshot_name)), "ro", "true"
                ], check=True)
                
                logging.info(
                    f"Snapshot {snapshot_name} sent to external drive successfully."
                )
                print(f"Snapshot {snapshot_name} sent to external drive successfully.")
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Error sending snapshot to external drive: {e}")
        print(f"Error sending snapshot to external drive: {e}", file=sys.stderr)
        # Try cleanup again if send failed due to space
        if "No space left on device" in str(e):
            logging.info("Attempting additional cleanup due to space error")
            cleanup_old_snapshots_for_size(snapshot_size)  # Free the same amount again
            # Could retry here, but for now just report the error


def receive_snapshot(snapshot_name):
    # Receive the snapshot from the external drive
    with subprocess.Popen(
        ["sudo", "btrfs", "send", external_drive_dir.joinpath(snapshot_name)],
        stdout=subprocess.PIPE,
    ) as send_proc:
        subprocess.run(
            ["sudo", "btrfs", "receive", local_snapshot_dir],
            stdin=send_proc.stdout,
            check=True,
        )
    print(f"Snapshot {snapshot_name} received from external drive successfully.")


def main():
    parser = argparse.ArgumentParser(
        description="Manage Btrfs snapshots between local system and external drive."
    )
    parser.add_argument(
        "-s",
        "--save",
        action="store_true",
        help="Save a snapshot of the root filesystem to an external drive.",
    )
    parser.add_argument(
        "-r",
        "--recall",
        action="store_true",
        help="Recall a snapshot from an external drive to the local system.",
    )
    parser.add_argument("snapshot_name", type=str, help="The name of the snapshot.")

    args = parser.parse_args()

    if args.save == args.recall:
        print("Error: Choose either -s (save) or -r (recall), not both.")
        sys.exit(1)

    if args.save:
        create_snapshot(args.snapshot_name)
        send_snapshot(args.snapshot_name)

    if args.recall:
        receive_snapshot(args.snapshot_name)


if __name__ == "__main__":
    main()
