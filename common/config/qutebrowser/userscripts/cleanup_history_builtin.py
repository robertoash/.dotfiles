"""Builtin history cleanup using qutebrowser's Python environment.

This module is imported directly by config.py, so it uses qutebrowser's
bundled Python which includes sqlite3 on Nix installations.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


def cleanup_old_history(config_datadir, days=30):
    """Delete history entries older than specified days.

    Args:
        config_datadir: Path to qutebrowser's data directory (from config.datadir)
        days: Number of days of history to keep (default: 30)

    Returns:
        str: Status message about cleanup results
        None: If history database doesn't exist
    """
    data_dir = Path(config_datadir)
    history_db = data_dir / "history.sqlite"

    if not history_db.exists():
        return None

    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_timestamp = int(cutoff_date.timestamp())

    conn = sqlite3.connect(str(history_db))
    cursor = conn.cursor()

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
        return f"History cleanup: Removed {total_deleted} entries older than {days} days"
    else:
        return f"No history entries older than {days} days found"
