#!/usr/bin/env python3
import os
import subprocess

# Define directories for icons
# iDIR = os.path.expanduser("~/.config/swaync/icons")


def get_mic_volume():
    # Retrieve the current microphone volume percentage
    result = subprocess.run(
        ["pactl", "get-source-volume", "@DEFAULT_SOURCE@"],
        capture_output=True,
        text=True,
    )
    volume = int(result.stdout.split()[4].replace("%", ""))
    # Check mute state
    result = subprocess.run(
        ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"], capture_output=True, text=True
    )
    muted = "yes" in result.stdout
    if muted:
        return "Muted"
    else:
        return f"{volume}%"


# def get_mic_icon():
#     current_volume = get_mic_volume()
#     if current_volume == "Muted":
#         return f"{iDIR}/microphone-mute.png"
#     else:
#         return f"{iDIR}/microphone.png"


def notify_mic_user():
    volume = get_mic_volume()
    # icon = get_mic_icon()
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
            # "-i",
            # icon,
            f"Mic-Level: {volume}",
        ]
    )


def inc_mic_volume():
    muted = get_mic_volume() == "Muted"
    if muted:
        toggle_mic()
    else:
        subprocess.run(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", "+5%"])
        notify_mic_user()


def dec_mic_volume():
    muted = get_mic_volume() == "Muted"
    if muted:
        toggle_mic()
    else:
        subprocess.run(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", "-5%"])
        notify_mic_user()


def toggle_mic():
    result = subprocess.run(
        ["pactl", "get-source-mute", "@DEFAULT_SOURCE@"], capture_output=True, text=True
    )
    if "yes" in result.stdout:
        subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"])
        subprocess.run(
            [
                "notify-send",
                "-e",
                "-u",
                "low",
                # "-i",
                # f"{iDIR}/microphone-mute.png",
                "Microphone Switched OFF",
            ]
        )
    else:
        subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"])
        subprocess.run(
            [
                "notify-send",
                "-e",
                "-u",
                "low",
                # "-i",
                # get_mic_icon(),
                "Microphone Switched ON",
            ]
        )


if __name__ == "__main__":
    import sys

    command = sys.argv[1] if len(sys.argv) > 1 else "--get"
    if command == "--get":
        print(get_mic_volume())
    elif command == "--inc":
        inc_mic_volume()
    elif command == "--dec":
        dec_mic_volume()
    elif command == "--toggle":
        toggle_mic()
