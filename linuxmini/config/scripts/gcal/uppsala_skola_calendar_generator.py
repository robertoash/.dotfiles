#!/usr/bin/env python3
"""
Uppsala School Schedule Generator
Generates gcalcli commands to add school schedule events to Google Calendar
Simply defines holidays - all other weekdays become "Uppsala - Skola"
"""

from datetime import datetime, timedelta
import subprocess
import sys

# Holiday periods - everything else on weekdays is school
HOLIDAYS = {
    # 2026
    "2026-06-13": {
        "end": "2026-08-17",
        "title": "Uppsala - Sommarlov",
    },  # Summer break after June 12
    "2026-09-25": {"end": "2026-09-25", "title": "Uppsala - Lovdag"},
    "2026-10-26": {"end": "2026-10-30", "title": "Uppsala - Höstlov"},
    "2026-12-23": {"end": "2027-01-12", "title": "Uppsala - Jullov"},
    # 2027
    "2027-02-22": {"end": "2027-02-26", "title": "Uppsala - Sportlov"},
    "2027-03-30": {"end": "2027-04-02", "title": "Uppsala - Påsklov"},
    "2027-04-30": {"end": "2027-04-30", "title": "Uppsala - Lovdag"},
    "2027-05-07": {
        "end": "2027-05-07",
        "title": "Uppsala - Lovdag (Kristi himmelsfärd)",
    },
    "2027-06-11": {"end": "2027-06-11", "title": "Uppsala - Studenten"},
    "2027-06-12": {"end": "2027-08-16", "title": "Uppsala - Sommarlov"},
    "2027-09-24": {"end": "2027-09-24", "title": "Uppsala - Lovdag"},
    "2027-11-01": {"end": "2027-11-05", "title": "Uppsala - Höstlov"},
    "2027-12-23": {"end": "2028-01-11", "title": "Uppsala - Jullov"},
    # 2028
    "2028-02-21": {"end": "2028-02-25", "title": "Uppsala - Sportlov"},
    "2028-03-10": {"end": "2028-03-10", "title": "Uppsala - Lovdag"},
    "2028-04-10": {"end": "2028-04-13", "title": "Uppsala - Påsklov"},
    "2028-04-30": {"end": "2028-04-30", "title": "Uppsala - Lovdag"},
    "2028-05-07": {
        "end": "2028-05-07",
        "title": "Uppsala - Lovdag (Kristi himmelsfärd)",
    },
    "2028-06-09": {"end": "2028-06-09", "title": "Uppsala - Studenten"},
    "2028-06-14": {
        "end": "2028-08-15",
        "title": "Uppsala - Sommarlov",
    },  # Summer break after school ends
}

# School period boundaries - can be overridden by command line args
DEFAULT_SCHOOL_START = "2026-06-12"  # Start from where you left off
DEFAULT_SCHOOL_END = "2028-06-13"  # End of schedule

# Calendar name - change this if you want to use a different calendar
CALENDAR_NAME = "Uppsala Skola"


def get_holiday_dates():
    """Get set of all holiday dates"""
    holiday_dates = set()

    for start_date, holiday_info in HOLIDAYS.items():
        end_date = holiday_info["end"]
        current = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        while current <= end:
            holiday_dates.add(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

    return holiday_dates


def get_school_weekdays(start_date=None, end_date=None):
    """Get all weekdays that are not holidays within the specified date range"""
    if start_date is None:
        start_date = DEFAULT_SCHOOL_START
    if end_date is None:
        end_date = DEFAULT_SCHOOL_END

    holiday_dates = get_holiday_dates()
    school_dates = []

    current = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        # If it's a weekday (Mon-Fri) and not a holiday
        if current.weekday() < 5 and date_str not in holiday_dates:
            school_dates.append(date_str)
        current += timedelta(days=1)

    return school_dates


def create_weekly_blocks(dates):
    """Group consecutive weekdays into weekly Mon-Fri blocks"""
    if not dates:
        return []

    blocks = []
    current_block_start = dates[0]
    current_block_end = dates[0]

    for i in range(1, len(dates)):
        current_date = datetime.strptime(dates[i], "%Y-%m-%d")
        prev_date = datetime.strptime(dates[i - 1], "%Y-%m-%d")

        # Check if this is the next consecutive weekday
        expected_next_day = prev_date + timedelta(days=1)

        # Special case: if previous day was Friday, next weekday should be Monday (3 days later)
        if prev_date.weekday() == 4:  # Friday
            expected_next_day = prev_date + timedelta(days=3)  # Monday

        if current_date == expected_next_day:
            # Continuous weekday, but check if we're crossing into a new week
            if prev_date.weekday() == 4:  # Previous was Friday, this is Monday
                # End the current block on Friday and start a new block on Monday
                blocks.append((current_block_start, dates[i - 1]))
                current_block_start = dates[i]
                current_block_end = dates[i]
            else:
                # Same week, extend the current block
                current_block_end = dates[i]
        else:
            # Gap found, save current block and start new one
            blocks.append((current_block_start, current_block_end))
            current_block_start = dates[i]
            current_block_end = dates[i]

    # Add the last block
    blocks.append((current_block_start, current_block_end))

    return blocks


def get_holidays_in_range(start_date, end_date):
    """Get holidays that fall within the specified date range"""
    holidays_in_range = {}

    range_start = datetime.strptime(start_date, "%Y-%m-%d")
    range_end = datetime.strptime(end_date, "%Y-%m-%d")

    for holiday_start, holiday_info in HOLIDAYS.items():
        holiday_end = holiday_info["end"]

        holiday_start_dt = datetime.strptime(holiday_start, "%Y-%m-%d")
        holiday_end_dt = datetime.strptime(holiday_end, "%Y-%m-%d")

        # Check if holiday overlaps with our date range
        if holiday_start_dt <= range_end and holiday_end_dt >= range_start:
            # Clip holiday to our range
            clipped_start = max(holiday_start_dt, range_start).strftime("%Y-%m-%d")
            clipped_end = min(holiday_end_dt, range_end).strftime("%Y-%m-%d")

            holidays_in_range[clipped_start] = {
                "end": clipped_end,
                "title": holiday_info["title"],
            }

    return holidays_in_range


def calculate_duration(start_date, end_date):
    """Calculate duration in days between two dates (inclusive)"""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return (end - start).days + 1


def generate_commands(start_date=None, end_date=None):
    """Generate gcalcli commands for the schedule within the specified date range"""
    if start_date is None:
        start_date = DEFAULT_SCHOOL_START
    if end_date is None:
        end_date = DEFAULT_SCHOOL_END

    commands = []

    # 1. Add holiday events (weekday blocks Mon-Fri, same as school events)
    holidays_in_range = get_holidays_in_range(start_date, end_date)
    for holiday_start, holiday_info in holidays_in_range.items():
        holiday_end = holiday_info["end"]
        title = holiday_info["title"]

        # Get only weekdays for this holiday period
        holiday_weekdays = []
        current = datetime.strptime(holiday_start, "%Y-%m-%d")
        end = datetime.strptime(holiday_end, "%Y-%m-%d")

        while current <= end:
            if current.weekday() < 5:  # Monday-Friday only
                holiday_weekdays.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        # Create weekly Mon-Fri blocks for holidays
        if holiday_weekdays:
            holiday_blocks = create_weekly_blocks(holiday_weekdays)

            for block_start, block_end in holiday_blocks:
                duration = calculate_duration(block_start, block_end)
                cmd = f'gcalcli --calendar "{CALENDAR_NAME}" add --title "{title}" --when "{block_start}" --allday --duration {duration} --noprompt'
                commands.append(cmd)

    # 2. Add school events (weekday blocks Mon-Fri) within our range
    school_dates = get_school_weekdays(start_date, end_date)
    school_blocks = create_weekly_blocks(school_dates)

    for block_start, block_end in school_blocks:
        duration = calculate_duration(block_start, block_end)
        cmd = f'gcalcli --calendar "{CALENDAR_NAME}" add --title "Uppsala - Skola" --when "{block_start}" --allday --duration {duration} --noprompt'
        commands.append(cmd)

    return commands


def print_schedule_summary(start_date=None, end_date=None):
    """Print a summary of the generated schedule"""
    if start_date is None:
        start_date = DEFAULT_SCHOOL_START
    if end_date is None:
        end_date = DEFAULT_SCHOOL_END

    # Get holidays in range (weekdays only)
    holidays_in_range = get_holidays_in_range(start_date, end_date)
    holiday_weekdays = set()
    for holiday_start, holiday_info in holidays_in_range.items():
        holiday_end = holiday_info["end"]
        current = datetime.strptime(holiday_start, "%Y-%m-%d")
        end = datetime.strptime(holiday_end, "%Y-%m-%d")
        while current <= end:
            if current.weekday() < 5:  # Only count weekdays
                holiday_weekdays.add(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

    school_dates = get_school_weekdays(start_date, end_date)

    print(f"Schedule Summary ({start_date} to {end_date}):")
    print(f"  Holiday weekdays: {len(holiday_weekdays)}")
    print(f"  School days: {len(school_dates)}")
    print(f"  Holiday periods: {len(holidays_in_range)}")

    school_blocks = create_weekly_blocks(school_dates)
    print(f"  School blocks: {len(school_blocks)}")
    print()

    if holidays_in_range:
        print("Holiday periods in range (weekdays only):")
        for holiday_start, holiday_info in sorted(holidays_in_range.items()):
            print(
                f"  {holiday_start} to {holiday_info['end']}: {holiday_info['title']}"
            )
        print()


def execute_commands(commands, dry_run=True):
    """Execute the gcalcli commands"""
    if dry_run:
        print("DRY RUN - Commands that would be executed:")
        print("=" * 50)

        # Count holiday vs school commands
        holiday_commands = [cmd for cmd in commands if "Uppsala - Skola" not in cmd]
        school_commands = [cmd for cmd in commands if "Uppsala - Skola" in cmd]

        if holiday_commands:
            print("HOLIDAY EVENTS:")
            for i, cmd in enumerate(holiday_commands, 1):
                print(f"{i:2d}. {cmd}")

        if school_commands:
            print("\nSCHOOL EVENTS:")
            for i, cmd in enumerate(school_commands, 1):
                print(f"{i:2d}. {cmd}")

        print(
            f"\nTotal commands: {len(commands)} ({len(holiday_commands)} holidays, {len(school_commands)} school blocks)"
        )
        print("\nTo execute for real, run with --execute flag")
    else:
        print(f"Executing {len(commands)} commands...")
        for i, cmd in enumerate(commands, 1):
            print(f"Executing {i}/{len(commands)}: {cmd}")
            try:
                # Just run the command as-is, let gcalcli handle authentication
                result = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True, timeout=60
                )
                if result.returncode != 0:
                    print(f"ERROR: {result.stderr.strip()}")
                    print(f"STDOUT: {result.stdout.strip()}")
                else:
                    print("SUCCESS")
                    if result.stdout.strip():
                        print(f"OUTPUT: {result.stdout.strip()}")
            except subprocess.TimeoutExpired:
                print("ERROR: Command timed out after 60 seconds")
            except Exception as e:
                print(f"ERROR executing command: {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Uppsala school schedule events"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute commands (default: dry run)",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show schedule summary only"
    )
    parser.add_argument(
        "--from", dest="from_date", help="Start date (YYYY-MM-DD, default: 2026-06-12)"
    )
    parser.add_argument(
        "--to", dest="to_date", help="End date (YYYY-MM-DD, default: 2028-06-13)"
    )

    args = parser.parse_args()

    # Use provided dates or defaults
    start_date = args.from_date or DEFAULT_SCHOOL_START
    end_date = args.to_date or DEFAULT_SCHOOL_END

    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Error: Dates must be in YYYY-MM-DD format")
        sys.exit(1)

    if args.summary:
        print_schedule_summary(start_date, end_date)
        return

    print_schedule_summary(start_date, end_date)
    commands = generate_commands(start_date, end_date)
    execute_commands(commands, not args.execute)


if __name__ == "__main__":
    main()
