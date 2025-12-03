#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SCREENSHOT_DIR = Path.home() / "images/screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now().strftime("%Y-%m-%d-%H%M%S")


def run(cmd, input_data=None):
    subprocess.run(cmd, shell=True, check=True, input=input_data)


def show_save_notification(filename, screenshot_type):
    """Show a notification with option to open directory in yazi."""
    action_cmd = (
        f'ACTION=$(dunstify -a "grim" -A "open,Open Directory" '
        f'"Screenshot Saved" "{screenshot_type} saved to {filename}"); '
        f'[ "$ACTION" = "open" ] && wezterm start --class yazi-term -- '
        f'/home/rash/.cargo/bin/yazi "{SCREENSHOT_DIR}"'
    )
    run(f"({action_cmd}) &")


def get_region_selection():
    """Get region selection from slurp, handle cancellation gracefully."""
    try:
        result = subprocess.check_output("slurp", shell=True, stderr=subprocess.DEVNULL)
        return result.decode().strip()
    except subprocess.CalledProcessError:
        print("Selection cancelled")
        sys.exit(0)


def region_annotate():
    # Create a temp file for the initial screenshot
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_path = temp_file.name
    out_path = SCREENSHOT_DIR / f"annotated-{STAMP}.png"
    region = get_region_selection()
    run(f'grim -g "{region}" "{temp_path}"')
    run(f'swappy -f "{temp_path}" -o "{out_path}"')
    # Optionally, delete temp file after use
    try:
        Path(temp_path).unlink()
    except Exception:
        pass


def region_direct_save():
    out_path = SCREENSHOT_DIR / f"region-{STAMP}.png"
    region = get_region_selection()
    run(f'grim -g "{region}" "{out_path}"')
    # Show notification with option to open directory
    show_save_notification(out_path.name, "Region")


def clipboard():
    region = get_region_selection()
    p1 = subprocess.Popen(f'grim -g "{region}" -', shell=True, stdout=subprocess.PIPE)
    subprocess.run("wl-copy", shell=True, stdin=p1.stdout)
    if p1.stdout:
        p1.stdout.close()
    p1.wait()
    # Show notification for clipboard action
    run('dunstify -a "grim" "Screenshot Copied" "Screenshot copied to clipboard"')


def get_window_geometry():
    """Get the geometry of the active window."""
    try:
        # Get window info as JSON
        window_info = (
            subprocess.check_output("hyprctl activewindow -j", shell=True)
            .decode()
            .strip()
        )

        # Extract geometry using jq
        jq_expr = (
            '(.at[0] | tostring) + "," + (.at[1] | tostring) + " " + '
            '(.size[0] | tostring) + "x" + (.size[1] | tostring)'
        )
        geom = (
            subprocess.check_output(
                f"echo '{window_info}' | jq -r '{jq_expr}'", shell=True
            )
            .decode()
            .strip()
        )

        return geom
    except subprocess.CalledProcessError:
        print("Failed to get window geometry")
        sys.exit(1)


def window_direct_save():
    out_path = SCREENSHOT_DIR / f"window-{STAMP}.png"
    geom = get_window_geometry()
    run(f'grim -g "{geom}" "{out_path}"')
    # Show notification with option to open directory
    show_save_notification(out_path.name, "Window")


def window_clipboard():
    geom = get_window_geometry()
    p1 = subprocess.Popen(f'grim -g "{geom}" -', shell=True, stdout=subprocess.PIPE)
    subprocess.run("wl-copy", shell=True, stdin=p1.stdout)
    if p1.stdout:
        p1.stdout.close()
    p1.wait()
    # Show notification for clipboard action
    run('dunstify -a "grim" "Screenshot Copied" "Screenshot copied to clipboard"')


def window_annotate():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_path = temp_file.name
    out_path = SCREENSHOT_DIR / f"annotated-{STAMP}.png"
    geom = get_window_geometry()
    run(f'grim -g "{geom}" "{temp_path}"')
    run(f'swappy -f "{temp_path}" -o "{out_path}"')
    try:
        Path(temp_path).unlink()
    except Exception:
        pass


def monitor_direct_save():
    out_path = SCREENSHOT_DIR / f"monitor-{STAMP}.png"
    monitor = (
        subprocess.check_output(
            "hyprctl monitors -j | jq -r '.[] | select(.focused) | .name'", shell=True
        )
        .decode()
        .strip()
    )
    run(f'grim -o "{monitor}" "{out_path}"')
    # Show notification with option to open directory
    show_save_notification(out_path.name, "Monitor")


def monitor_annotate():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        temp_path = temp_file.name
    out_path = SCREENSHOT_DIR / f"annotated-{STAMP}.png"
    monitor = (
        subprocess.check_output(
            "hyprctl monitors -j | jq -r '.[] | select(.focused) | .name'", shell=True
        )
        .decode()
        .strip()
    )
    run(f'grim -o "{monitor}" "{temp_path}"')
    run(f'swappy -f "{temp_path}" -o "{out_path}"')
    try:
        Path(temp_path).unlink()
    except Exception:
        pass


def desktop_direct_save():
    out_path = SCREENSHOT_DIR / f"desktop-{STAMP}.png"
    run(f'grim "{out_path}"')
    # Show notification with option to open directory
    show_save_notification(out_path.name, "Desktop")


actions = {
    "region-annotate": region_annotate,
    "region-direct-save": region_direct_save,
    "clipboard": clipboard,
    "window-clipboard": window_clipboard,
    "window-annotate": window_annotate,
    "window-direct-save": window_direct_save,
    "monitor-direct-save": monitor_direct_save,
    "monitor-annotate": monitor_annotate,
    "desktop-direct-save": desktop_direct_save,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in actions:
        print("Usage: take_screenshot.py [ACTION]")
        print("Actions: region-annotate, region-direct-save, clipboard,")
        print("         window-annotate, window-direct-save,")
        print("         monitor-direct-save, monitor-annotate,")
        print("         desktop-direct-save")
        sys.exit(1)
    actions[sys.argv[1]]()
