#!/usr/bin/env python3
import subprocess
import sys

# Power menu items: (label, command)
POWER_ITEMS = [
    ("lock", "hyprlock --immediate"),
    ("logout", "hyprctl dispatch exit"),
    ("reboot", "systemctl reboot"),
    ("power_off", "systemctl poweroff"),
]


def launch_rofi(items):
    """Show rofi menu and return selected item"""
    menu_text = "\n".join([label for label, _ in items])

    result = subprocess.run(
        ["rofi", "-dmenu", "-i", "-theme-str", 'entry { placeholder: "Shutdown actions..."; }'],
        input=menu_text.encode(),
        stdout=subprocess.PIPE,
    )

    return result.stdout.decode().strip()


def main():
    choice = launch_rofi(POWER_ITEMS)

    if not choice:
        sys.exit(0)

    # Find the command for the selected label
    command = None
    for label, cmd in POWER_ITEMS:
        if label == choice:
            command = cmd
            break

    if command:
        subprocess.run(command, shell=True)
    else:
        print(f"Unknown choice: {choice}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
