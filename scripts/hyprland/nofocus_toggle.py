#!/usr/bin/env python3

import json
import subprocess


# Function to execute a shell command and return the output
def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


# Get the active window's address and pin status
active_window_json = run_command("hyprctl activewindow -j")
active_window = json.loads(active_window_json)
window_id = active_window.get("address")
floating = active_window.get("floating")
pinned = active_window.get("pinned")

if floating and pinned:
    run_command(f"hyprctl setprop address:{window_id} nofocus 1")
    # append window_id to nofocus_windows file
    with open("/tmp/nofocus_windows", "a") as f:
        f.write(window_id + "\n")
else:
    try:
        # get nofocus_windows from file
        with open("/tmp/nofocus_windows") as f:
            nofocus_windows = f.read().splitlines()

        if not nofocus_windows:
            # Failsafe: If the file is empty, run `setprop nofocus 0` on every client
            all_clients_json = run_command("hyprctl clients -j")
            all_clients = json.loads(all_clients_json)
            for client in all_clients:
                run_command(f"hyprctl setprop address:{client['address']} nofocus 0")
        else:
            updated_windows = []
            for window in nofocus_windows:
                result = run_command(f"hyprctl setprop address:{window} nofocus 0")
                if "ok" not in result:
                    updated_windows.append(window)

            # Rewrite the file with windows that were not successfully updated
            with open("/tmp/nofocus_windows", "w") as f:
                f.write("\n".join(updated_windows))

    except FileNotFoundError:
        pass  # If the file doesn't exist, there's nothing to do
