#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
import sys

from _utils import logging_utils

logging_utils.configure_logging()

# Define the locations
home_dir = os.path.expanduser("~")
local_snapshot_dir = os.path.join(home_dir, ".local/.snapshots")
external_drive_dir = "/mnt/.snapshots"


def create_snapshot(snapshot_name):
    # Create a read-only local snapshot
    subprocess.run(
        [
            "sudo",
            "btrfs",
            "subvolume",
            "snapshot",
            "-r",
            "/",
            f"{local_snapshot_dir}/{snapshot_name}",
        ],
        check=True,
    )
    logging.info(
        f"Snapshot {snapshot_name} created successfully in {local_snapshot_dir}"
    )
    print(f"Snapshot {snapshot_name} created successfully in {local_snapshot_dir}")


def send_snapshot(snapshot_name):
    # Ensure the snapshot directory exists and is a Btrfs filesystem
    if not os.path.isdir(f"{local_snapshot_dir}/{snapshot_name}"):
        logging.error(
            f"Snapshot directory {local_snapshot_dir}/{snapshot_name} does not exist."
        )
        print(
            f"Snapshot directory {local_snapshot_dir}/{snapshot_name} does not exist."
        )
        return

    send_command = ["sudo", "btrfs", "send", f"{local_snapshot_dir}/{snapshot_name}"]
    receive_command = ["sudo", "btrfs", "receive", external_drive_dir]

    # Open a subprocess for 'btrfs send'
    with subprocess.Popen(send_command, stdout=subprocess.PIPE) as send_proc:
        if send_proc.stdout is not None:
            # Use the output of 'btrfs send' as input for 'btrfs receive'
            subprocess.run(receive_command, stdin=send_proc.stdout, check=True)
            logging.info(
                f"Snapshot {snapshot_name} sent to external drive successfully."
            )
            print(f"Snapshot {snapshot_name} sent to external drive successfully.")


def receive_snapshot(snapshot_name):
    # Receive the snapshot from the external drive
    with subprocess.Popen(
        ["sudo", "btrfs", "send", os.path.join(external_drive_dir, snapshot_name)],
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
