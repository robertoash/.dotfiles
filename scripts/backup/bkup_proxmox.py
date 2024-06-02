#!/usr/bin/env python3

import logging
import os
import subprocess
import time

from _utils import logging_utils


def backup_proxmox():
    remote_host = "proxmox"
    remote_backup_dir = "/mnt/vm_backups/dump"
    local_backup_dir = "/media/sda1/server_bkups/proxmox"

    logging_utils.configure_logging()

    try:
        # Ensure the local backup directory exists
        if not os.path.exists(local_backup_dir):
            os.makedirs(local_backup_dir)
            logging.info("[bkup_proxmox]: Created local backup directory")

        start_time = time.time()

        # Run rsync to sync backups from Proxmox to local directory
        rsync_command = [
            "rsync",
            "-avz",
            "--delete",
            f"{remote_host}:{remote_backup_dir}/",
            f"{local_backup_dir}/",
        ]
        subprocess.run(rsync_command, check=True)

        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        logging.info(
            f"[bkup_proxmox]: Backup completed successfully in {int(minutes)}m{int(seconds)}s"
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"[bkup_proxmox]: ERROR during backup: {e}")


if __name__ == "__main__":
    backup_proxmox()
