#!/usr/bin/env python3

import logging
import os
import subprocess
import time

from _utils import logging_utils


def backup_old_hp():
    remote_host = "oldhp"
    remote_backup_dir = "/mnt/usb_bkups/oldhp_backups"
    local_backup_dir = "/media/sda1/server_bkups/old_hp"

    logging_utils.configure_logging()

    try:
        # Ensure the local backup directory exists
        if not os.path.exists(local_backup_dir):
            os.makedirs(local_backup_dir)
            logging.info("[bkup_oldhp]: Created local backup directory")

        start_time = time.time()

        # Run rsync to sync backups from old_hp to local directory
        rsync_command = [
            "rsync",
            "-aHvz",
            "--progress",
            "--delete",
            f"{remote_host}:{remote_backup_dir}/",
            f"{local_backup_dir}/",
        ]
        subprocess.run(rsync_command, check=True)

        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        logging.info(
            f"[bkup_oldhp]: Backup completed successfully in "
            f"{int(minutes)}m{int(seconds)}s"
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"[bkup_oldhp]: ERROR during backup: {e}")


if __name__ == "__main__":
    backup_old_hp()
