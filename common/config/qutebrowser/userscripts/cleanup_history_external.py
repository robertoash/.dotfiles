#!/usr/bin/env python3
"""Cleanup old qutebrowser history entries using system Python with sqlite3."""

import os
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path


def cleanup_old_history(data_dir, days=30):
    """Delete history entries older than specified days."""
    history_db = Path(data_dir) / "history.sqlite"

    if not history_db.exists():
        print(f"History database not found at {history_db}")
        return

    # Calculate cutoff timestamp (qutebrowser uses seconds since epoch)
    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_timestamp = int(cutoff_date.timestamp())

    # Connect to database
    conn = sqlite3.connect(str(history_db))
    cursor = conn.cursor()

    # Delete old entries from both tables
    cursor.execute("DELETE FROM History WHERE atime < ?", (cutoff_timestamp,))
    deleted_history = cursor.rowcount

    cursor.execute(
        "DELETE FROM CompletionHistory WHERE last_atime < ?", (cutoff_timestamp,)
    )
    deleted_completion = cursor.rowcount

    conn.commit()
    conn.close()

    total_deleted = deleted_history + deleted_completion
    if total_deleted > 0:
        print(f"History cleanup: Removed {total_deleted} entries older than {days} days")
    else:
        print(f"No history entries older than {days} days found")


if __name__ == "__main__":
    # Get data directory from environment variable set by qutebrowser
    data_dir = os.environ.get("QUTE_DATA_DIR")

    if not data_dir:
        # Fallback to default location
        data_dir = str(Path.home() / ".local/share/qutebrowser")

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30

    try:
        cleanup_old_history(data_dir, days)
    except Exception as e:
        print(f"History cleanup failed: {e}", file=sys.stderr)
        sys.exit(1)
