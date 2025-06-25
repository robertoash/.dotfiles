#!/usr/bin/env python3
"""
Google Calendar Persistent Notifications using gcalcli and dunstify
Based on implementations from the gcalcli community
"""

import argparse
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from hashlib import md5
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CONFIGURATION - Edit these settings to customize behavior
# ============================================================================

# Calendar Configuration
CALENDARS_TO_MONITOR = ["Gmail Kalender", "Hem"]  # List of calendar names to monitor

# Notification Timing Configuration
NOTIFICATION_INTERVALS = [
    {
        "minutes": 10,
        "persistent": False,
        "urgency": "low",
        "sound": False,
    },
    {
        "minutes": 5,
        "persistent": True,
        "urgency": "normal",
        "sound": False,
    },
    {
        "minutes": 0,
        "persistent": True,
        "urgency": "critical",
        "sound": True,
    },
]

# Notification Appearance
NOTIFICATION_ID_BASE = 7400
ICON = "calendar"
SOUND_FILE = "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"

# Action Configuration
PROFILE_SELECTOR_SCRIPT = "/home/rash/.config/scripts/rofi/rofi_profile_selector.py"
DEFAULT_BROWSER = "vivaldi"  # Default browser for meeting links
SNOOZE_MINUTES = 5  # How many minutes to snooze notifications

# File Paths
CONFIG_DIR = Path.home() / ".config" / "gcal-notifications"
NOTIFICATION_LOG = CONFIG_DIR / "notifications.log"

# ============================================================================
# END CONFIGURATION
# ============================================================================

# Create config directory
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class CalendarNotifier:
    """Main class for handling Google Calendar notifications with dunstify"""

    def __init__(self, config_dir: Path = None):
        self.reminder_intervals = [
            interval["minutes"] for interval in NOTIFICATION_INTERVALS
        ]
        self.config_dir = config_dir or CONFIG_DIR
        self.notification_log = self.config_dir / "notifications.log"

        # Create config directory
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def add_calendar_filters(self, cmd: List[str]) -> List[str]:
        """Add calendar filters to gcalcli command"""
        if CALENDARS_TO_MONITOR:
            for calendar in CALENDARS_TO_MONITOR:
                cmd.extend(["--calendar", calendar])
        return cmd

    def run_gcalcli(self, command: List[str]) -> str:
        """Execute gcalcli command and return output"""
        try:
            # Add calendar filters to the command
            command = self.add_calendar_filters(command)

            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"gcalcli command failed: {' '.join(command)}")
            logger.error(f"Error: {e.stderr}")
            return ""
        except FileNotFoundError:
            logger.error("gcalcli not found. Please install gcalcli first.")
            return ""

    def get_event_id(self, event_text: str) -> str:
        """Generate unique ID for event"""
        return md5(event_text.encode()).hexdigest()[:12]

    def get_notification_config(self, minutes: int) -> Dict:
        """Get notification configuration for specific reminder time"""
        for interval in NOTIFICATION_INTERVALS:
            if interval["minutes"] == minutes:
                return interval

        # Default fallback
        return {
            "minutes": minutes,
            "persistent": True,
            "urgency": "normal",
            "sound": True,
        }

    def get_timeout(self, persistent: bool) -> int:
        """Get notification timeout based on persistence setting"""
        return 0 if persistent else 5000  # 0 = persistent, 5000 = 5 seconds

    def extract_meeting_url(self, event_text: str) -> Optional[str]:
        """Extract meeting URL from event text"""
        url_pattern = r"https://[^\s]+"
        match = re.search(url_pattern, event_text)
        return match.group(0) if match else None

    def play_notification_sound(self, should_play: bool = True):
        """Play notification sound if available and requested"""
        if not should_play:
            return

        if Path(SOUND_FILE).exists():
            try:
                subprocess.Popen(
                    ["paplay", SOUND_FILE],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.debug("Notification sound played")
            except FileNotFoundError:
                logger.debug("paplay not available, skipping sound")
        else:
            logger.debug(f"Sound file not found: {SOUND_FILE}")

    def format_notification_message(
        self, event_title: str, remind_minutes: int
    ) -> Tuple[str, str]:
        """Format notification title and message"""
        title = "📅 Calendar Reminder"

        if remind_minutes == 0:
            message = f"🔔 Starting now: {event_title}"
        elif remind_minutes == 1:
            message = f"⏰ In 1 minute: {event_title}"
        else:
            message = f"⏰ In {remind_minutes} minutes: {event_title}"

        return title, message

    def handle_notification_action(
        self, action: str, event_text: str, remind_minutes: int, meeting_url: str = None
    ):
        """Handle user actions from notification"""
        logger.info(f"Notification action triggered: {action}")

        if action == "dismiss":
            # Just log the dismissal - notification is already closed
            logger.info(f"Event dismissed: {event_text}")

        elif action == "snooze":
            # Schedule a new notification in SNOOZE_MINUTES
            logger.info(f"Snoozing event for {SNOOZE_MINUTES} minutes: {event_text}")
            subprocess.Popen(
                [
                    "sh",
                    "-c",
                    f"sleep {SNOOZE_MINUTES * 60} && {sys.executable} {__file__} "
                    f"--notify-event '{event_text}' --minutes 0",
                ]
            )

        elif action == "open_meeting" and meeting_url:
            # Use rofi profile selector to choose browser/profile
            logger.info(f"Opening meeting URL with profile selector: {meeting_url}")
            logger.debug(f"Profile selector script path: {PROFILE_SELECTOR_SCRIPT}")
            logger.debug(f"Script exists: {Path(PROFILE_SELECTOR_SCRIPT).exists()}")
            self.open_meeting_with_profile_selector(meeting_url)

    def open_meeting_with_profile_selector(self, meeting_url: str):
        """Open meeting URL using the rofi profile selector"""
        try:
            # Let user choose the browser via rofi
            browsers = ["qutebrowser", "vivaldi", "chromium"]
            logger.info("Showing browser selection dialog...")

            browser_choice = subprocess.run(
                ["rofi", "-dmenu", "-i", "-p", "Choose browser:"],
                input="\n".join(browsers),
                text=True,
                capture_output=True,
                env=dict(os.environ, DISPLAY=":0"),  # Ensure DISPLAY is set
            )

            if browser_choice.returncode != 0 or not browser_choice.stdout.strip():
                logger.info("Browser selection cancelled")
                return

            selected_browser = browser_choice.stdout.strip()
            logger.info(f"User selected browser: {selected_browser}")

            if Path(PROFILE_SELECTOR_SCRIPT).exists():
                # Launch profile selector which will handle the profile choice and opening
                env = os.environ.copy()
                env["MEETING_URL"] = meeting_url
                env["DISPLAY"] = ":0"  # Ensure DISPLAY is set for GUI apps

                logger.info(f"Launching profile selector for {selected_browser}...")
                result = subprocess.run(
                    ["python3", PROFILE_SELECTOR_SCRIPT, selected_browser],
                    env=env,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    logger.error(f"Profile selector failed: {result.stderr}")
                    # Fallback to default browser
                    subprocess.Popen(["xdg-open", meeting_url])
                else:
                    logger.info(f"Meeting opened successfully with {selected_browser}")

            else:
                # Fallback: open directly with default browser
                logger.warning(
                    f"Profile selector not found at {PROFILE_SELECTOR_SCRIPT}, "
                    "using default browser"
                )
                subprocess.Popen(["xdg-open", meeting_url])

        except Exception as e:
            logger.error(f"Error opening meeting with profile selector: {e}")
            # Final fallback
            subprocess.Popen(["xdg-open", meeting_url])

    def send_notification_simple(
        self, event_text: str, remind_minutes: int, meeting_url: str = None
    ):
        """Send notification without duplicate checking (for cron usage)"""
        # Get notification configuration for this reminder time
        config = self.get_notification_config(remind_minutes)
        persistent = config["persistent"]
        urgency = config["urgency"]
        play_sound = config["sound"]

        event_id = self.get_event_id(event_text)
        timeout = self.get_timeout(persistent)

        # Format notification
        title, message = self.format_notification_message(event_text, remind_minutes)

        # Add meeting link info to message
        if meeting_url:
            message += "\n🔗 Meeting link available"

        # Play sound first, before showing notification
        self.play_notification_sound(play_sound)

        # Calculate notification ID
        notification_id = NOTIFICATION_ID_BASE + (int(event_id[:8], 16) % 1000)

        # Build dunstify command
        cmd = [
            "dunstify",
            "--replace",
            str(notification_id),
            "--urgency",
            urgency,
            "--timeout",
            str(timeout),
            "--icon",
            ICON,
            "--appname",
            "gcalcli",
        ]

        # Add actions based on notification type and content
        if meeting_url:
            cmd.extend(
                [
                    "--action",
                    "open_meeting,🔗 Open Meeting",
                    "--action",
                    "dismiss,❌ Dismiss",
                ]
            )
        else:
            cmd.extend(["--action", "dismiss,❌ Dismiss"])

        # Add snooze for non-critical notifications
        if urgency != "critical":
            cmd.extend(["--action", f"snooze,⏰ Snooze {SNOOZE_MINUTES}min"])

        # Add stack tag for grouping notifications
        cmd.extend(
            [
                "--hints",
                f"string:x-dunst-stack-tag:gcalcli-{event_id}",
            ]
        )

        cmd.extend([title, message])

        try:
            # Send notification and capture action response
            result = subprocess.run(cmd, capture_output=True, text=True)

            # Handle action if user clicked one
            if result.returncode == 0 and result.stdout.strip():
                raw_action = result.stdout.strip()
                logger.debug(f"Raw dunstify output: '{result.stdout}'")

                # Handle action index mapping (workaround for dunst returning indices)
                # Actions are added in this order in the cmd array:
                action_map = {}
                if meeting_url:
                    action_map["0"] = "open_meeting"  # First action
                    action_map["1"] = "dismiss"  # Second action
                    if urgency != "critical":
                        action_map["2"] = "snooze"  # Third action
                else:
                    action_map["0"] = "dismiss"  # First and only action
                    if urgency != "critical":
                        action_map["1"] = "snooze"  # Second action

                # Map action index to action name if needed
                action = action_map.get(raw_action, raw_action)
                logger.debug(f"Mapped action: '{raw_action}' -> '{action}'")

                self.handle_notification_action(
                    action, event_text, remind_minutes, meeting_url
                )

            logger.info(f"Notification sent: {title} - {message}")

        except FileNotFoundError:
            # Fallback to notify-send (no actions support)
            fallback_cmd = [
                "notify-send",
                "-u",
                urgency,
                "-t",
                str(timeout),
                "-i",
                ICON,
                title,
                message,
            ]
            subprocess.Popen(
                fallback_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            logger.info(f"Fallback notification sent: {title}")

    def check_events_at_exact_time(self, minutes: int):
        """Check for events starting at exactly the specified time from now"""
        # Calculate exact target time (when the event should start)
        now = datetime.now()
        target_time = now + timedelta(minutes=minutes)

        # Create a window that includes the target minute
        # Search from target minute to the next minute to catch events starting at target time
        start_time = target_time.replace(second=0, microsecond=0)
        end_time = start_time + timedelta(minutes=1)

        # Format times for gcalcli
        start_str = start_time.strftime("%Y-%m-%d %H:%M")
        end_str = end_time.strftime("%Y-%m-%d %H:%M")

        logger.debug(
            f"Checking for events starting between {start_str} and {end_str} "
            f"(target: {target_time.strftime('%Y-%m-%d %H:%M')})"
        )

        # Get events that START in this narrow window
        cmd = [
            "gcalcli",
            "agenda",
            "--details",
            "url",
            "--details",
            "location",
            "--tsv",
            start_str,
            end_str,
        ]
        output = self.run_gcalcli(cmd)

        if not output:
            logger.debug("No events found starting at target time")
            return

        logger.debug(f"Raw gcalcli output:\n{output}")

        # Parse TSV output and send notifications
        lines = output.split("\n")
        events_found = 0

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            logger.debug(f"Processing line {i}: {line}")

            # Skip header lines and "No Events Found" messages
            if (
                line.startswith("start_date")
                or line.startswith("No Events Found")
                or "start_time" in line
                or "end_time" in line
                or "html_link" in line
                or "title" in line
            ):
                logger.debug(f"Skipping header/info line: {line}")
                continue

            parts = line.split("\t")
            logger.debug(f"Split into {len(parts)} parts: {parts}")

            # Expected TSV format with --details url location:
            # 0:start_date  1:start_time  2:end_date  3:end_time  4:html_link
            # 5:hangout_link  6:title  7:location

            if len(parts) >= 7:  # Need at least 7 columns to have a title
                event_start_date = parts[0].strip()
                event_start_time = parts[1].strip()
                event_title = parts[6].strip()  # Title is in column 6

                # Skip if no real title
                if not event_title or event_title in ["title", ""]:
                    logger.debug("No valid title found, skipping")
                    continue

                # Parse the event start time to ensure it matches our target
                try:
                    event_datetime_str = f"{event_start_date} {event_start_time}"
                    event_datetime = datetime.strptime(
                        event_datetime_str, "%Y-%m-%d %H:%M"
                    )

                    # Check if this event starts within the target minute
                    target_minute = target_time.replace(second=0, microsecond=0)
                    event_minute = event_datetime.replace(second=0, microsecond=0)

                    if event_minute != target_minute:
                        logger.debug(
                            f"Event starts at {event_datetime}, target minute is {target_minute}, "
                            f"event minute is {event_minute} - skipping"
                        )
                        continue

                except ValueError as e:
                    logger.debug(
                        f"Could not parse event time '{event_datetime_str}': {e}"
                    )
                    continue

                event_text = event_title
                logger.debug(
                    f"Found event title: {event_title} starting at {event_datetime}"
                )

                # Add location if available (column 7)
                if len(parts) > 7 and parts[7].strip():
                    location = parts[7].strip()
                    event_text += f" at {location}"
                    logger.debug(f"Added location: {location}")

                # Extract URL if available (column 4 = html_link)
                meeting_url = None
                if len(parts) > 4 and parts[4].strip() and parts[4].startswith("http"):
                    meeting_url = parts[4].strip()
                    logger.debug(f"Found meeting URL: {meeting_url}")

                logger.info(
                    f"Found event starting at target time: {event_title} (full: {event_text})"
                )

                # Send notification immediately (no duplicate checking needed for cron)
                self.send_notification_simple(event_text, minutes, meeting_url)
                events_found += 1
            else:
                logger.debug(
                    f"Line has only {len(parts)} parts, need at least 7 for title"
                )

        if events_found == 0:
            logger.debug(
                f"No events found starting at exactly {target_time.strftime('%H:%M')}"
            )
        else:
            logger.debug(
                f"Processed {events_found} events for {minutes}-minute notification"
            )

    def run_cron_check(self):
        """Run single check for all reminder intervals (for cron jobs)"""
        calendars_str = (
            ", ".join(CALENDARS_TO_MONITOR) if CALENDARS_TO_MONITOR else "all calendars"
        )
        logger.info(f"Running cron check for calendar reminders on: {calendars_str}")
        logger.debug(f"Reminder intervals to check: {self.reminder_intervals}")

        for minutes in self.reminder_intervals:
            logger.debug(f"Checking for events at {minutes} minutes")
            self.check_events_at_exact_time(minutes)

        logger.debug("Cron check completed")

    def run_advanced_notifications(self, minutes: int = 10):
        """Advanced mode with detailed event information"""
        calendars_str = (
            ", ".join(CALENDARS_TO_MONITOR) if CALENDARS_TO_MONITOR else "all calendars"
        )
        logger.info(
            f"Checking for events in next {minutes} minutes on: {calendars_str}"
        )

        self.check_events_at_exact_time(minutes)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Google Calendar Persistent Notifications with dunstify",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Cron job (add to crontab -e):
  */1 * * * * DISPLAY=:0 python3 %(prog)s --cron

  # Check for events in next 15 minutes:
  python3 %(prog)s --advanced --minutes 15
        """,
    )

    # Add mutually exclusive group for main commands
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--cron", action="store_true", help="Run single check (for cron jobs)"
    )
    group.add_argument(
        "--advanced", action="store_true", help="Advanced mode with meeting links"
    )

    # Optional arguments
    parser.add_argument(
        "--minutes",
        type=int,
        default=10,
        help="Minutes to check ahead for advanced mode (default: 10)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create notifier instance
    notifier = CalendarNotifier()

    # Execute command
    if args.cron:
        notifier.run_cron_check()
    elif args.advanced:
        notifier.run_advanced_notifications(args.minutes)


if __name__ == "__main__":
    main()
