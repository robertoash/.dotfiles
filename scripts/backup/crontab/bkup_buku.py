#!/usr/bin/env python3

import logging
import os
import subprocess
import time

from _utils import logging_utils


def backup_buku():
    source_dir = os.path.expanduser("~/.local/share/buku/bkups")
    local_backup_dir = "/media/sda1/local_bkups/buku"

    logging_utils.configure_logging()

    try:
        # Ensure the local backup directory exists
        if not os.path.exists(local_backup_dir):
            os.makedirs(local_backup_dir)
            logging.info("[bkup_oldhp]: Created local backup directory")

        start_time = time.time()

        # Run rsync to sync backups from ~/.local/share/buku/bkups
        rsync_command = [
            "rsync",
            "-aHvz",
            "--progress",
            "--delete",
            f"{source_dir}/",
            f"{local_backup_dir}/",
        ]
        subprocess.run(rsync_command, check=True)

        end_time = time.time()
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        logging.info(
            f"[bkup_buku]: Backup completed successfully in "
            f"{int(minutes)}m{int(seconds)}s"
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"[bkup_buku]: ERROR during backup: {e}")


if __name__ == "__main__":
    backup_buku()
