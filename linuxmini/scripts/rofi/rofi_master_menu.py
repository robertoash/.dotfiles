#!/usr/bin/env python3
import subprocess
import sys

# Menu items: (label, command)
MENU_ITEMS = [
    ("⏻ Power Menu", "~/.config/scripts/rofi/rofi_power.py"),
    ("😀 Emoji Selector", "rofimoji --skin-tone medium-light -a clipboard copy --selector rofi --clipboarder wl-copy --typer wtype"),
    ("📺 IPTV", "~/.config/scripts/iptv/rofi_xtream.py"),
    ("🎬 Jellyfin", "~/.config/scripts/rofi/rofi_jellyfin.py"),
    ("📼 SVT Play", "~/.config/scripts/rofi/rofi_svtp.py"),
    ("▶ Youtube Watch Later", "~/.config/scripts/rofi/rofi_yt_watchlater.py"),
    ("⌨ Hyprland Keybinds", "~/.config/scripts/rofi/rofi_hypr_keybinds.py"),
]


def launch_rofi(items):
    """Show rofi menu and return selected item"""
    menu_text = "\n".join([label for label, _ in items])

    result = subprocess.run(
        ["rofi", "-dmenu", "-i", "-p", "Menus"],
        input=menu_text.encode(),
        stdout=subprocess.PIPE,
    )

    return result.stdout.decode().strip()


def main():
    choice = launch_rofi(MENU_ITEMS)

    if not choice:
        sys.exit(0)

    # Find the command for the selected label
    command = None
    for label, cmd in MENU_ITEMS:
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
