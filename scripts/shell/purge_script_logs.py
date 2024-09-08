import datetime
import os
from pathlib import Path


def purge_old_logs():
    log_dir = Path.home() / ".config" / "scripts" / "_logs"
    current_month = datetime.datetime.now().strftime("%Y-%m")

    for root, _, files in os.walk(log_dir):
        for file in files:
            file_path = Path(root) / file
            if current_month not in file:
                try:
                    file_path.unlink()
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")


if __name__ == "__main__":
    purge_old_logs()
