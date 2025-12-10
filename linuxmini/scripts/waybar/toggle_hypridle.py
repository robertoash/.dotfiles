#!/usr/bin/env python3
import argparse
import datetime
import subprocess
import sys
from pathlib import Path

STATUS_FILE = Path("/tmp/waybar/hypridle_status.json")
LOG_FILE = Path("/tmp/hypridle_toggle.log")


def kill_all_hypridle():
    """Stop hypridle systemd service."""
    subprocess.run(
        ["systemctl", "--user", "stop", "hypridle.service"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def is_hypridle_running():
    """Check if hypridle systemd service is active."""
    result = subprocess.run(
        ["systemctl", "--user", "is-active", "hypridle.service"],
        stdout=subprocess.PIPE
    )
    return result.returncode == 0


def log_action(action):
    """Log toggle actions with timestamp."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp} - {action}\n")
    except Exception:
        pass  # Don't fail if logging fails


def write_status(hypridle_is_on: bool):
    # ⚫ = running, 🔴 = off: because we want to show idle_inhibit status in waybar
    try:
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATUS_FILE.write_text("⚫" if hypridle_is_on else "🔴")
        log_action(f"Status written: {'⚫ (running)' if hypridle_is_on else '🔴 (off)'}")
    except Exception as e:
        log_action(f"Failed to write status: {e}")


def set_manual_override():
    """Set manual override flag and update idle detection status."""
    mqtt_dir = Path("/tmp/mqtt")
    mqtt_dir.mkdir(parents=True, exist_ok=True)

    # Write to MQTT files for Home Assistant
    mqtt_override_file = mqtt_dir / "manual_override_status"
    mqtt_override_file.write_text("active")

    # Update core idle detection status - user is actively overriding, so they're present
    (mqtt_dir / "linux_mini_status").write_text("active")
    (mqtt_dir / "idle_detection_status").write_text(
        "inactive"
    )  # idle detection stopped

    # Also call activity status reporter for consistency
    try:
        subprocess.run(
            [
                str(
                    Path(__file__).parent.parent / "ha" / "activity_status_reporter.py"
                ),
                "--active",
            ],
            check=False,
        )
    except Exception:
        pass  # Don't fail if reporter fails

    # Keep local file for immediate waybar updates
    override_file = Path("/tmp/waybar/manual_override")
    override_file.parent.mkdir(parents=True, exist_ok=True)
    override_file.write_text("override_active")

    log_action("Manual override ENABLED - hypridle disabled by user")


def clear_manual_override():
    """Clear manual override flag and reset idle detection status."""
    mqtt_dir = Path("/tmp/mqtt")
    mqtt_dir.mkdir(parents=True, exist_ok=True)

    # Write to MQTT files for Home Assistant
    mqtt_override_file = mqtt_dir / "manual_override_status"
    mqtt_override_file.write_text("inactive")

    # Reset core idle detection status - user is re-enabling, assume they're active
    (mqtt_dir / "linux_mini_status").write_text("active")
    (mqtt_dir / "idle_detection_status").write_text(
        "inactive"
    )  # idle detection ready but not running

    # Also call activity status reporter for consistency
    try:
        subprocess.run(
            [
                str(
                    Path(__file__).parent.parent / "ha" / "activity_status_reporter.py"
                ),
                "--active",
            ],
            check=False,
        )
    except Exception:
        pass  # Don't fail if reporter fails

    # Keep local file for immediate waybar updates
    override_file = Path("/tmp/waybar/manual_override")
    override_file.unlink(missing_ok=True)

    log_action("Manual override DISABLED - hypridle re-enabled by user")


def get_status():
    return is_hypridle_running()


def toggle_hypridle(hypridle_is_on: bool):
    if hypridle_is_on:
        kill_all_hypridle()
        set_manual_override()  # Set manual override when turning off
        log_action("Hypridle service stopped")
        return False
    else:
        # Start hypridle systemd service
        log_action("Starting hypridle service")
        subprocess.run(
            ["systemctl", "--user", "start", "hypridle.service"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        clear_manual_override()  # Clear manual override when turning on
        log_action("Hypridle service started")
        return True


def main():
    parser = argparse.ArgumentParser(description="Toggle hypridle on/off")
    parser.add_argument(
        "--fresh-start",
        action="store_true",
        help="Delete PID file if it exists, kill all hypridle, and turn hypridle on",
    )
    args = parser.parse_args()

    # Always log the script execution for debugging
    log_action(f"Script started with args: {' '.join(sys.argv)}")

    if args.fresh_start:
        log_action("Fresh start requested - ensuring hypridle service is stopped")
        kill_all_hypridle()
        hypridle_is_on = False
        log_action("Fresh start preparation complete")
    else:
        hypridle_is_on = get_status()

    hypridle_is_on = toggle_hypridle(hypridle_is_on)
    write_status(hypridle_is_on)

    # If we just started hypridle fresh, ensure activity status is properly reported
    if args.fresh_start and hypridle_is_on:
        log_action("Fresh start: ensuring activity status is reported")
        # Small delay to ensure hypridle is fully started, then verify it's running
        import time
        time.sleep(0.5)
        if is_hypridle_running():
            log_action("Fresh start: hypridle confirmed running, calling activity status reporter")
            try:
                subprocess.run(
                    [
                        str(
                            Path(__file__).parent.parent / "hyprland" / "idle_management" / "activity_status_reporter.py"
                        ),
                        "--active",
                    ],
                    check=False,
                )
                log_action("Fresh start: activity status reporter called successfully")
                
                # Force a file modification to ensure MQTT watchdog detects the change
                # This is needed because the watchdog might not be running yet at boot
                status_file = Path("/tmp/mqtt/linux_mini_status")
                if status_file.exists():
                    # Touch the file to trigger watchdog
                    status_file.touch()
                    log_action("Fresh start: touched linux_mini_status to trigger MQTT watchdog")
            except Exception as e:
                log_action(f"Fresh start: activity status reporter failed: {e}")
        else:
            log_action("Fresh start: hypridle not running after toggle, skipping activity status reporter")

    # Update waybar status to reflect the change
    try:
        subprocess.run(
            ["python3", str(Path(__file__).parent / "waybar_idle_status.py")],
            check=True,
        )
    except subprocess.CalledProcessError:
        print("Warning: Could not update waybar status")


if __name__ == "__main__":
    main()
