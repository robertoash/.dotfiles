#!/usr/bin/env python3
"""
Google Calendar Persistent Notifications using gcalcli and dunstify
Based on implementations from the gcalcli community
"""

import argparse
import json
import logging
import os
import re
import subprocess
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
NOTIFICATION_TIMEOUT = 5000  # 5 seconds

# Action Configuration
PROFILE_SELECTOR_SCRIPT = "/home/rash/.config/scripts/rofi/rofi_profile_selector.py"
SNOOZE_MINUTES = 1  # How many minutes to snooze notifications

# File Paths
CONFIG_DIR = Path.home() / ".config" / "gcal-notifications"
CACHE_FILE = CONFIG_DIR / "events_cache.json"

# Cache Configuration
CACHE_DURATION_HOURS = 1  # How long cache is considered fresh

# ============================================================================
# END CONFIGURATION
# ============================================================================

# Create config directory
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Setup logging - quiet by default, verbose only with --verbose flag
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors by default
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
        self.cache_file = self.config_dir / "events_cache.json"

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

    def get_event_id(self, event_title: str) -> str:
        """Generate unique ID for event"""
        return md5(event_title.encode()).hexdigest()[:12]

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
        return (
            0 if persistent else NOTIFICATION_TIMEOUT
        )  # 0 = persistent, 5000 = 5 seconds

    def extract_conference_url(
        self, hangout_link: str, description: str
    ) -> Optional[str]:
        """Extract conference URL from hangout_link or description"""
        # First check hangout_link for Google Meet
        if hangout_link and hangout_link.strip() and hangout_link.startswith("http"):
            return hangout_link.strip()

        # Then check description for various meeting platforms
        if not description:
            return None

        # Pattern for various meeting URLs
        patterns = [
            r"https://teams\.microsoft\.com/l/meetup-join/[^\s\n<>]+",  # Teams
            r"https://[^\.]+\.zoom\.us/j/[^\s\n<>]+",  # Zoom
            r"https://meet\.google\.com/[^\s\n<>]+",  # Google Meet
            r"https://[^\.]+\.webex\.com/[^\s\n<>]+",  # Webex
            # Custom platforms like Legora
            r"https://careers\.[^\.]+\.com/video_meetings/[^\s\n<>]+",
            r"https://[^\s\n<>]*meeting[^\s\n<>]*",  # Generic meeting URLs
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def is_physical_location(self, location: str) -> bool:
        """Check if location appears to be a physical location rather than a URL or other data"""
        if not location:
            return False

        location = location.strip()

        # Check if it's a URL
        if location.startswith(("http://", "https://", "www.")):
            return False

        # Check if it contains URL-like patterns
        url_patterns = [
            r"https?://",
            r"www\.",
            r"\.com/",
            r"\.org/",
            r"\.net/",
            r"/[a-zA-Z0-9_-]+",  # URL path-like segments
        ]

        for pattern in url_patterns:
            if re.search(pattern, location, re.IGNORECASE):
                return False

        # Check if it looks like a meeting platform identifier
        meeting_indicators = [
            "meeting_",
            "video_meetings",
            "meetup-join",
            "zoom.us",
            "teams.microsoft.com",
            "meet.google.com",
        ]

        for indicator in meeting_indicators:
            if indicator.lower() in location.lower():
                return False

        # If it passes all checks, assume it's a physical location
        return True

    def format_location_for_maps(self, location: str) -> str:
        """Format location for Google Maps URL if it's a physical location"""
        if not location or not self.is_physical_location(location):
            return None
        # Clean up the location and encode for URL
        import urllib.parse

        cleaned_location = location.strip()
        encoded_location = urllib.parse.quote(cleaned_location)
        return f"https://maps.google.com/maps?q={encoded_location}"

    def is_cache_fresh(self) -> bool:
        """Check if the cache file exists and is fresh"""
        if not self.cache_file.exists():
            return False

        try:
            cache_mtime = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
            cache_age = datetime.now() - cache_mtime
            is_fresh = cache_age < timedelta(hours=CACHE_DURATION_HOURS)
            logger.debug(f"Cache age: {cache_age}, fresh: {is_fresh}")
            return is_fresh
        except Exception as e:
            logger.error(f"Error checking cache freshness: {e}")
            return False

    def load_cached_events(self) -> Dict:
        """Load events from cache file"""
        if not self.cache_file.exists():
            logger.debug("Cache file does not exist")
            return {}

        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)
                logger.debug(f"Loaded {len(data.get('events', []))} events from cache")
                return data
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
            return {}

    def save_events_to_cache(self, events: List[Dict]):
        """Save events to cache file"""
        try:
            cache_data = {"last_updated": datetime.now().isoformat(), "events": events}
            with open(self.cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Cached {len(events)} events")
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def fetch_and_cache_events(self) -> None:
        """Fetch events from gcalcli and cache them for future queries"""
        logger.debug("Refreshing event cache from Google Calendar API")

        # Get events for the next 24 hours to ensure we catch all needed events
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=24)

        start_str = start_time.strftime("%Y-%m-%d")
        end_str = end_time.strftime("%Y-%m-%d")

        cmd = [
            "gcalcli",
            "agenda",
            "--details",
            "url",
            "--details",
            "location",
            "--details",
            "description",
            "--tsv",
            start_str,
            end_str,
        ]

        output = self.run_gcalcli(cmd)
        if not output:
            logger.warning("No events fetched from gcalcli")
            self.save_events_to_cache([])
            return

        events = []
        lines = output.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip header lines
            if (
                line.startswith("start_date")
                or line.startswith("No Events Found")
                or "start_time" in line
                or "end_time" in line
                or "html_link" in line
                or "title" in line
                or "description" in line
            ):
                continue

            parts = line.split("\t")
            if len(parts) >= 7:
                try:
                    event_start_date = parts[0].strip()
                    event_start_time = parts[1].strip()
                    event_title = parts[6].strip()

                    if not event_title or event_title in ["title", ""]:
                        continue

                    # Parse event datetime
                    event_datetime_str = f"{event_start_date} {event_start_time}"
                    event_datetime = datetime.strptime(
                        event_datetime_str, "%Y-%m-%d %H:%M"
                    )

                    # Extract location (column 7) and validate if it's a physical location
                    location = parts[7].strip() if len(parts) > 7 else None
                    maps_url = (
                        self.format_location_for_maps(location) if location else None
                    )

                    # Extract event URL (column 4 = html_link)
                    event_url = parts[4].strip() if len(parts) > 4 else None

                    # Extract hangout link (column 5)
                    hangout_link = parts[5].strip() if len(parts) > 5 else None

                    # Extract description (column 8)
                    description = parts[8].strip() if len(parts) > 8 else None

                    # Extract conference URL
                    conference_url = self.extract_conference_url(
                        hangout_link, description
                    )

                    # Create event record
                    event = {
                        "title": event_title,
                        "start_time": event_datetime.isoformat(),
                        "event_url": event_url,
                        "conference_url": conference_url,
                        "maps_url": maps_url,
                    }
                    events.append(event)

                except ValueError as e:
                    logger.debug(f"Could not parse event line: {line} - {e}")
                    continue

        self.save_events_to_cache(events)
        logger.debug(f"Successfully cached {len(events)} events")

    def check_cached_notifications(self) -> None:
        """Check cached events and send notifications based on simple minute matching"""
        cache_data = self.load_cached_events()
        if not cache_data or "events" not in cache_data:
            logger.warning("No cached events available")
            return

        current_time = datetime.now()
        logger.debug(f"Checking cached events for notifications at {current_time}")

        for event in cache_data["events"]:
            try:
                event_time = datetime.fromisoformat(event["start_time"])

                # Check each notification interval
                for minutes in self.reminder_intervals:
                    # Calculate when this notification should be sent
                    notification_time = event_time - timedelta(minutes=minutes)

                    # Simple minute-based matching - if current minute matches notification minute
                    if (
                        current_time.hour == notification_time.hour
                        and current_time.minute == notification_time.minute
                    ):

                        logger.debug(
                            f"Sending {minutes}-minute notification for: {event['title']}"
                        )
                        self.send_notification_simple(event, minutes)

            except Exception as e:
                logger.error(f"Error processing cached event: {e}")

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

    def handle_notification_action(self, action: str, event: Dict, remind_minutes: int):
        """Handle user actions from notification"""
        logger.info(f"Notification action triggered: {action}")

        if action == "dismiss":
            # Just log the dismissal - notification is already closed
            logger.info(f"Event dismissed: {event['title']}")

        elif action == "snooze":
            # Schedule a new notification in SNOOZE_MINUTES
            logger.info(
                f"Snoozing event for {SNOOZE_MINUTES} minutes: {event['title']}"
            )
            # Note: Implementing proper snooze by re-caching the event with updated time
            # The old approach with --notify-event was broken as that argument doesn't exist

        elif action == "open_event" and event.get("event_url"):
            # Open Google Calendar event
            logger.info(f"Opening Google Calendar event: {event['event_url']}")
            subprocess.Popen(["xdg-open", event["event_url"]])

        elif action == "open_location" and event.get("maps_url"):
            # Open location in Google Maps
            logger.info(f"Opening location in Google Maps: {event['maps_url']}")
            subprocess.Popen(["xdg-open", event["maps_url"]])

        elif action == "open_conference" and event.get("conference_url"):
            # Use rofi profile selector to choose browser/profile for conference
            logger.info(
                f"Opening conference URL with profile selector: {event['conference_url']}"
            )
            self.open_meeting_with_profile_selector(event["conference_url"])

    def open_meeting_with_profile_selector(self, meeting_url: str):
        """Open meeting URL using the rofi profile selector"""
        try:
            # Let user choose the browser via rofi
            browsers = ["qutebrowser", "vivaldi", "brave"]
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

    def send_notification_simple(self, event: Dict, remind_minutes: int):
        """Send notification using dunstify (duplicates handled by --replace)"""
        # Get notification configuration for this reminder time
        config = self.get_notification_config(remind_minutes)
        persistent = config["persistent"]
        urgency = config["urgency"]
        play_sound = config["sound"]

        event_id = self.get_event_id(event["title"])
        timeout = self.get_timeout(persistent)

        # Format notification
        title, message = self.format_notification_message(
            event["title"], remind_minutes
        )

        # Add additional info to message
        info_parts = []
        if event.get("conference_url"):
            info_parts.append("🔗 Conference link available")
        if event.get("maps_url"):
            info_parts.append("📍 Location available")

        if info_parts:
            message += "\n" + " • ".join(info_parts)

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

        # Build actions based on available data
        actions = []

        # Always add snooze and dismiss for non-critical notifications
        if urgency != "critical":
            actions.extend(
                [
                    f"snooze,⏰ Snooze {SNOOZE_MINUTES} min",
                ]
            )

        actions.append("dismiss,❌ Dismiss")

        # Add event-specific actions
        if event.get("event_url"):
            actions.append("open_event,📅 Open Event in Google Calendar")

        if event.get("conference_url"):
            actions.append("open_conference,🔗 Join Meeting")

        if event.get("maps_url"):
            actions.append("open_location,🗺️ Open Meeting Location in Maps")

        # Add actions to command
        for action in actions:
            cmd.extend(["--action", action])

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

                # WORKAROUND: Dunst bug - right-click dismiss returns numeric indices
                # When using context menu (left/middle click), dunst returns action names
                # When right-clicking to dismiss, it returns numbers
                # We only process non-numeric responses (actual action names)
                if raw_action.isdigit():
                    logger.debug(f"Ignoring numeric response '{raw_action}' - likely a right-click dismiss")
                else:
                    # This is a real action selection from the context menu
                    logger.debug(f"Processing action: '{raw_action}'")
                    self.handle_notification_action(raw_action, event, remind_minutes)

            logger.debug(f"Notification sent: {title} - {message}")

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
            logger.debug(f"Fallback notification sent: {title}")

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
            "--details",
            "description",
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
                or "description" in line
            ):
                logger.debug(f"Skipping header/info line: {line}")
                continue

            parts = line.split("\t")
            logger.debug(f"Split into {len(parts)} parts: {parts}")

            # Expected TSV format with --details url location description:
            # 0:start_date  1:start_time  2:end_date  3:end_time  4:html_link
            # 5:hangout_link  6:title  7:location  8:description

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

                logger.debug(
                    f"Found event title: {event_title} starting at {event_datetime}"
                )

                # Extract location (column 7) and validate if it's a physical location
                location = parts[7].strip() if len(parts) > 7 else None
                maps_url = self.format_location_for_maps(location) if location else None

                if maps_url:
                    logger.debug(f"Added valid physical location: {location}")

                # Extract event URL (column 4 = html_link)
                event_url = parts[4].strip() if len(parts) > 4 else None

                # Extract hangout link (column 5)
                hangout_link = parts[5].strip() if len(parts) > 5 else None

                # Extract description (column 8)
                description = parts[8].strip() if len(parts) > 8 else None

                # Extract conference URL
                conference_url = self.extract_conference_url(hangout_link, description)

                # Create event object
                event = {
                    "title": event_title,
                    "event_url": event_url,
                    "conference_url": conference_url,
                    "maps_url": maps_url,
                }

                logger.debug(f"Found event starting at target time: {event_title}")

                # Send notification immediately (no duplicate checking needed for cron)
                self.send_notification_simple(event, minutes)
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
        """Run single check for all reminder intervals (for cron jobs) - now uses cache"""
        calendars_str = (
            ", ".join(CALENDARS_TO_MONITOR) if CALENDARS_TO_MONITOR else "all calendars"
        )
        logger.debug(f"Running cron check for calendar reminders on: {calendars_str}")

        # Check if cache is fresh, if not, refresh it
        if not self.is_cache_fresh():
            logger.debug("Cache is stale or missing, refreshing...")
            self.fetch_and_cache_events()

        # Check cached events for notifications
        self.check_cached_notifications()
        logger.debug("Cron check completed")

    def run_advanced_notifications(self, minutes: int = 10):
        """Advanced mode with detailed event information"""
        calendars_str = (
            ", ".join(CALENDARS_TO_MONITOR) if CALENDARS_TO_MONITOR else "all calendars"
        )
        logger.debug(
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
  # Refresh cache (add to crontab every 30 minutes):
  */30 * * * * DISPLAY=:0 python3 %(prog)s --refresh

  # Query cache for notifications (add to crontab every minute):
  */1 * * * * DISPLAY=:0 python3 %(prog)s --query

  # Old cron job (still works but less efficient):
  */1 * * * * DISPLAY=:0 python3 %(prog)s --cron

  # Check for events in next 15 minutes:
  python3 %(prog)s --advanced --minutes 15
        """,
    )

    # Add mutually exclusive group for main commands
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh event cache from API (run every 30 minutes)",
    )
    group.add_argument(
        "--query",
        action="store_true",
        help="Query cached events for notifications (run every minute)",
    )
    group.add_argument(
        "--cron",
        action="store_true",
        help="Run single check with smart caching (backward compatibility)",
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
    else:
        # Ensure we're at WARNING level for normal operations (quiet mode)
        logging.getLogger().setLevel(logging.WARNING)

    # Create notifier instance
    notifier = CalendarNotifier()

    # Execute command
    if args.refresh:
        notifier.fetch_and_cache_events()
    elif args.query:
        notifier.check_cached_notifications()
    elif args.cron:
        notifier.run_cron_check()
    elif args.advanced:
        notifier.run_advanced_notifications(args.minutes)


if __name__ == "__main__":
    main()
