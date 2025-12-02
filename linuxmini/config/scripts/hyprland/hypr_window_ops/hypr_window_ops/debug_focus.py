#!/usr/bin/env python3

import json
import subprocess
import sys


def run_hyprctl(command):
    """Run a hyprctl command and return the parsed JSON output."""
    result = subprocess.run(["hyprctl"] + command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {' '.join(command)}: {result.stderr}")
        return None

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw output: {result.stdout[:100]}...")
        return None


def debug_monitors_and_windows():
    """Print detailed debug info about monitors and windows."""
    print("=== DEBUG INFO ===")

    # Check monitors
    print("\n=== MONITORS ===")
    monitors = run_hyprctl(["monitors", "-j"])
    if not monitors:
        print("No monitors detected or error getting monitor info!")
        return

    print(f"Found {len(monitors)} monitor(s):")
    for i, mon in enumerate(monitors):
        print(
            f"  Monitor {i+1}: name={mon.get('name')}, x={mon.get('x')}, y={mon.get('y')}, "
            f"width={mon.get('width')}, height={mon.get('height')}, "
            f"transform={mon.get('transform', 0)}"
        )

    # Sort monitors by x-coordinate for left/right detection
    sorted_monitors = sorted(monitors, key=lambda m: m.get("x", 0))
    if sorted_monitors:
        print("\nMonitor identification:")
        print(f"  Left monitor would be: {sorted_monitors[0].get('name')}")
        if len(sorted_monitors) > 1:
            print(f"  Right monitor would be: {sorted_monitors[-1].get('name')}")

    # Check windows
    print("\n=== WINDOWS ===")
    clients = run_hyprctl(["clients", "-j"])
    if not clients:
        print("No windows detected or error getting window info!")
        return

    print(f"Found {len(clients)} window(s):")
    for i, client in enumerate(clients):
        print(
            f"  Window {i+1}: title='{client.get('title', 'unknown')[:30]}...', "
            f"class={client.get('class', 'unknown')}, monitor={client.get('monitor', 'unknown')}, "
            f"workspace={client.get('workspace', {}).get('id', 'unknown')}, "
            f"at={client.get('at', [0, 0])}"
        )

    # Check windows by monitor
    print("\n=== WINDOWS BY MONITOR ===")
    for mon in monitors:
        mon_name = mon.get("name")
        mon_windows = [c for c in clients if c.get("monitor") == mon_name]
        print(f"Monitor {mon_name}: {len(mon_windows)} window(s)")

        if mon_windows:
            # Test sorting
            print(
                f"  Sorting for monitor {mon_name} (transform={mon.get('transform', 0)}):"
            )
            is_vertical = mon.get("transform", 0) in [1, 3]

            if is_vertical:
                # Vertical sort (y first, then x)
                mon_windows.sort(
                    key=lambda w: (w.get("at", [0, 0])[1], w.get("at", [0, 0])[0])
                )
                sort_type = "vertical (y,x)"
            else:
                # Horizontal sort (x first, then y)
                mon_windows.sort(
                    key=lambda w: (w.get("at", [0, 0])[0], w.get("at", [0, 0])[1])
                )
                sort_type = "horizontal (x,y)"

            print(f"  Sorted {sort_type}:")
            for i, window in enumerate(mon_windows):
                position = "master" if i == 0 else f"slave{i}"
                print(
                    f"    {position}: '{window.get('title', 'unknown')[:30]}...', "
                    f"at={window.get('at', [0, 0])}"
                )


def main():
    """Main entry point for debugging."""
    debug_monitors_and_windows()
    return 0


if __name__ == "__main__":
    sys.exit(main())
