#!/usr/bin/env python3

import subprocess


def backup_old_hp():
    remote_host = "10.20.10.95"
    remote_user = "root"
    remote_backup_dir = (
        "/home/rash/bkups"  # Change this to the actual backup directory on old_hp
    )
    local_backup_dir = "/media/sda1/server_bkups/old_hp"

    # Ensure the local backup directory exists
    subprocess.run(["mkdir", "-p", local_backup_dir], check=True)

    # Run rsync to sync backups from old_hp to local directory
    rsync_command = [
        "rsync",
        "-avz",
        "--delete",
        f"{remote_user}@{remote_host}:{remote_backup_dir}/",
        f"{local_backup_dir}/",
    ]
    subprocess.run(rsync_command, check=True)


if __name__ == "__main__":
    backup_old_hp()
