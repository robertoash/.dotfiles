#!/usr/bin/env python3

import subprocess


def backup_proxmox():
    remote_host = "10.20.10.80"
    remote_user = "root"
    remote_backup_dir = "/mnt/vm_backups/dump"
    local_backup_dir = "/media/sda1/server_bkups/proxmox"

    # Ensure the local backup directory exists
    subprocess.run(["mkdir", "-p", local_backup_dir], check=True)

    # Run rsync to sync backups from Proxmox to local directory
    rsync_command = [
        "rsync",
        "-avz",
        "--delete",
        f"{remote_user}@{remote_host}:{remote_backup_dir}/",
        f"{local_backup_dir}/",
    ]
    subprocess.run(rsync_command, check=True)


if __name__ == "__main__":
    backup_proxmox()
