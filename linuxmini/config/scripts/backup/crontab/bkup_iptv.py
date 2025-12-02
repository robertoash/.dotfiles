#!/usr/bin/env python3

import logging
import os
import subprocess
import sys
import time

# Add the custom script path to PYTHONPATH
sys.path.append("/home/rash/.config/scripts")
from _utils import logging_utils  # noqa: E402

logging_utils.configure_logging()


def bkup_iptv():
    remote_host = "dockerlab"
    remote_backup_dir = "/root/dev/docker_data/iptv_server/html/"
    local_backup_dir = "/media/sda1/server_bkups/iptv_server/"
    extensions = ["m3u", "xml", "json"]

    # ✅ Build include args properly as a list
    include_args = ["--include=*/"] + [f"--include=*.{ext}" for ext in extensions]
    exclude_arg = "--exclude=*"

    try:
        if not os.path.exists(local_backup_dir):
            os.makedirs(local_backup_dir)
            logging.info("[bkup_iptv]: Created local backup directory")

        start_time = time.time()

        rsync_command = [
            "rsync",
            "-avz",
            "--progress",
            "--delete",
            *include_args,  # 💥 unpack the list, not a string
            exclude_arg,
            f"{remote_host}:{remote_backup_dir}",
            f"{local_backup_dir}",
        ]
        subprocess.run(rsync_command, check=True)

        end_time = time.time()
        minutes, seconds = divmod(end_time - start_time, 60)
        logging.info(
            f"[bkup_iptv]: Backup completed successfully in {int(minutes)}m{int(seconds)}s"
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"[bkup_iptv]: ERROR during backup: {e}")


if __name__ == "__main__":
    bkup_iptv()
