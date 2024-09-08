import datetime
import os
from pathlib import Path


def purge_old_logs():
    import re

    log_dir = Path.home() / ".config" / "scripts" / "_logs"
    current_month = datetime.datetime.now().strftime("%Y-%m")
    date_pattern = re.compile(r"\d{4}-\d{2}")

    deleted_files = []
    kept_files = []

    for root, _, files in os.walk(log_dir):
        for file in files:
            file_path = Path(root) / file
            if date_pattern.search(file) and current_month not in file:
                try:
                    file_path.unlink()
                    deleted_files.append(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
            else:
                kept_files.append(file_path)

    # Present summary
    print(f"Deleted {len(deleted_files)} files.")
    print(f"Kept {len(kept_files)} files.")


if __name__ == "__main__":
    purge_old_logs()
