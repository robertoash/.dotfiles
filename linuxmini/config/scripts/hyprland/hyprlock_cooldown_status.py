#!/usr/bin/env python3
"""
Hyprlock Cooldown Status Display

Checks faillock status and displays cooldown information for hyprlock.
Shows remaining lockout time and current failure count.
"""

import subprocess
import os
import re
from datetime import datetime, timedelta


def get_faillock_status(username=None):
    """Get faillock status for the specified user."""
    if username is None:
        username = os.getenv("USER", "unknown")

    try:
        result = subprocess.run(
            ["faillock", "--user", username],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


def parse_lockout_info(faillock_output):
    """Parse faillock output to extract lockout information."""
    lines = faillock_output.strip().split("\n")

    total_failures = 0
    most_recent_failure = None

    for line in lines:
        # Count failures by looking for lines that start with a date and end with 'V' (valid)
        line = line.strip()
        if line and line[0].isdigit():  # Lines starting with a digit (date)
            # Check if this is a valid failure (ends with 'V')
            if line.endswith("V"):
                total_failures += 1
                # Keep track of the most recent failure
                most_recent_failure = line

    return total_failures, most_recent_failure


def read_faillock_config():
    """Read deny and unlock_time from faillock.conf."""
    try:
        with open("/etc/security/faillock.conf", "r") as f:
            content = f.read()

        # Extract deny value (default 3)
        deny_match = re.search(r"^deny\s*=\s*(\d+)", content, re.MULTILINE)
        deny = int(deny_match.group(1)) if deny_match else 3

        # Extract unlock_time value (default 600)
        unlock_match = re.search(r"^unlock_time\s*=\s*(\d+)", content, re.MULTILINE)
        unlock_time = int(unlock_match.group(1)) if unlock_match else 600

        return deny, unlock_time
    except Exception:
        # Fallback to defaults if file can't be read
        return 3, 600


def parse_most_recent_failure_time(most_recent_failure):
    """Parse timestamp from most recent failure line."""
    if not most_recent_failure:
        return None

    try:
        # Extract timestamp from line like "2024-01-20 15:30:45  TTY  /dev/pts/0  V"
        timestamp_str = (
            most_recent_failure.split()[0] + " " + most_recent_failure.split()[1]
        )
        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def get_cooldown_display():
    """Get the display string for current cooldown status."""
    username = os.getenv("USER")
    faillock_output = get_faillock_status(username)

    if not faillock_output:
        return ""

    failures, most_recent_failure = parse_lockout_info(faillock_output)
    deny, unlock_time = read_faillock_config()

    if failures >= deny:
        # Account is locked - show countdown if possible
        last_failure_time = parse_most_recent_failure_time(most_recent_failure)
        if last_failure_time:
            # Calculate remaining lockout time
            unlock_at = last_failure_time + timedelta(seconds=unlock_time)
            now = datetime.now()
            if now < unlock_at:
                remaining = int((unlock_at - now).total_seconds())
                return f"Failed attempts: {failures}/{deny} ({remaining}s remaining)"
            else:
                # Lockout period has expired
                return f"Failed attempts: {failures}/{deny}"
        else:
            # Can't parse time, just show locked status
            return f"🔒 LOCKED: {failures}/{deny}"
    elif failures > 0:
        # Show failure count with limit
        return f"Failed attempts: {failures}/{deny}"
    else:
        # No failures
        return ""


def main():
    """Main function to output cooldown status."""
    try:
        status = get_cooldown_display()
        print(status)
    except Exception as e:
        # Fail silently for hyprlock display
        print(e)


if __name__ == "__main__":
    main()
