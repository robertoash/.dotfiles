#!/usr/bin/env python3
import os
import subprocess


def get_volume():
    # Retrieve the current volume percentage
    result = subprocess.run(
        ["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True
    )
    volume = int(result.stdout.split()[4].replace("%", ""))
    # Check mute state
    result = subprocess.run(
        ["pactl", "get-sink-mute", "@DEFAULT_SINK@"], capture_output=True, text=True
    )
    muted = "yes" in result.stdout
    if muted:
        return "Muted"
    else:
        return f"{volume}%"


def notify_user():
    volume = get_volume()
    if volume == "Muted":
        subprocess.run(
            [
                "notify-send",
                "-e",
                "-h",
                "string:x-canonical-private-synchronous:volume_notif",
                "-u",
                "low",
                "Volume: Muted",
            ]
        )
    else:
        subprocess.run(
            [
                "notify-send",
                "-e",
                "-h",
                f"int:value:{volume.replace('%', '')}",
                "-h",
                "string:x-canonical-private-synchronous:volume_notif",
                "-u",
                "low",
                f"Volume: {volume}",
            ]
        )


def inc_volume():
    muted = get_volume() == "Muted"
    if muted:
        toggle_mute()
    else:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"])
        notify_user()


def dec_volume():
    muted = get_volume() == "Muted"
    if muted:
        toggle_mute()
    else:
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"])
        notify_user()


def toggle_mute():
    result = subprocess.run(
        ["pactl", "get-sink-mute", "@DEFAULT_SINK@"], capture_output=True, text=True
    )
    if "yes" in result.stdout:
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
        subprocess.run(
            [
                "notify-send",
                "-e",
                "-u",
                "low",
                "Volume Switched OFF",
            ]
        )
    else:
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])
        subprocess.run(
            [
                "notify-send",
                "-e",
                "-u",
                "low",
                "Volume Switched ON",
            ]
        )


if __name__ == "__main__":
    import sys

    command = sys.argv[1] if len(sys.argv) > 1 else "--get"
    if command == "--get":
        print(get_volume())
    elif command == "--inc":
        inc_volume()
    elif command == "--dec":
        dec_volume()
    elif command == "--toggle":
        toggle_mute()
