#!/usr/bin/env python3

import logging
import os
import re
import subprocess
import time

from _utils import logging_utils


def _get_rsync_transfer_size(rsync_args):
    """Dry-run rsync to estimate bytes to transfer. Returns None on failure."""
    result = subprocess.run(
        rsync_args + ["--dry-run", "--stats"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    match = re.search(r"Total transferred file size:\s+([\d,]+)", result.stdout)
    return int(match.group(1).replace(",", "")) if match else None


def _ensure_space_available(local_backup_dir, required_bytes):
    """Delete zero-byte then oldest local backups until enough space is free."""
    buffer = 2 * 1024 ** 3  # 2GB safety buffer
    needed = required_bytes + buffer

    stat = os.statvfs(local_backup_dir)
    if stat.f_bavail * stat.f_frsize >= needed:
        return

    free_gb = stat.f_bavail * stat.f_frsize / 1e9
    need_gb = needed / 1e9
    logging.info(
        f"[bkup_oldhp]: {free_gb:.1f}GB free, need {need_gb:.1f}GB — "
        "removing old backups to make space"
    )

    files = [
        os.path.join(local_backup_dir, f)
        for f in os.listdir(local_backup_dir)
        if os.path.isfile(os.path.join(local_backup_dir, f))
    ]
    # Zero-byte files first (they're failed transfers), then oldest by mtime
    files.sort(key=lambda f: (os.path.getsize(f) != 0, os.path.getmtime(f)))

    for fpath in files:
        stat = os.statvfs(local_backup_dir)
        if stat.f_bavail * stat.f_frsize >= needed:
            break
        size = os.path.getsize(fpath)
        logging.info(
            f"[bkup_oldhp]: Removing {os.path.basename(fpath)} "
            f"({size / 1e9:.2f}GB)"
        )
        os.remove(fpath)

    stat = os.statvfs(local_backup_dir)
    free_after = stat.f_bavail * stat.f_frsize
    if free_after < required_bytes:
        logging.warning(
            f"[bkup_oldhp]: Still only {free_after / 1e9:.1f}GB free after cleanup "
            f"(need {required_bytes / 1e9:.1f}GB) — rsync may fail"
        )


def backup_old_hp():
    remote_host = "oldhp"
    remote_backup_dir = "/mnt/lvm_backups/oldhp_backups"
    local_backup_dir = "/media/sda1/server_bkups/oldhp"

    logging_utils.configure_logging()

    try:
        if not os.path.exists(local_backup_dir):
            os.makedirs(local_backup_dir)
            logging.info("[bkup_oldhp]: Created local backup directory")

        rsync_args = [
            "rsync",
            "-aHvz",
            "--progress",
            "--delete",
            f"{remote_host}:{remote_backup_dir}/",
            f"{local_backup_dir}/",
        ]

        transfer_size = _get_rsync_transfer_size(rsync_args)
        if transfer_size is None:
            # Fall back to size of largest existing local backup as estimate
            local_files = [
                os.path.join(local_backup_dir, f)
                for f in os.listdir(local_backup_dir)
                if os.path.isfile(os.path.join(local_backup_dir, f))
            ]
            transfer_size = max(
                (os.path.getsize(f) for f in local_files), default=0
            )
            logging.warning(
                f"[bkup_oldhp]: Could not estimate transfer size via dry-run, "
                f"using {transfer_size / 1e9:.1f}GB fallback"
            )

        if transfer_size > 0:
            _ensure_space_available(local_backup_dir, transfer_size)

        start_time = time.time()
        subprocess.run(rsync_args, check=True)
        elapsed = time.time() - start_time
        minutes, seconds = divmod(elapsed, 60)
        logging.info(
            f"[bkup_oldhp]: Backup completed successfully in "
            f"{int(minutes)}m{int(seconds)}s"
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"[bkup_oldhp]: ERROR during backup: {e}")


if __name__ == "__main__":
    backup_old_hp()
