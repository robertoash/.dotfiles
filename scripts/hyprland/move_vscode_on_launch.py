#!/usr/bin/env python3

import subprocess
import time
import json

# Delay in seconds to wait before moving windows
DELAY = 5
# # Size as a percentage of the screen to resize the VSCode window when 2 windows are open
# size_percentage = "exact 100% 65%"


# Workspace assignments for VS Code windows
# Adjust according to your workspace names and the titles of your VS Code windows
workspace_assignments = {
    "tienda (Workspace)": 2,
    "dbt-models (Workspace)": 2,
    "personal (Workspace)": 1
}

def get_windows():
    """Get a list of all windows from hyprctl."""
    try:
        output = subprocess.check_output(["hyprctl", "clients", "-j"], text=True)
        return json.loads(output)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching windows: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []

def get_windows_in_workspace(workspace):
    """Get a list of all windows in a specified workspace."""
    try:
        output = subprocess.check_output(["hyprctl", "workspaces", "-j"], text=True)
        json_output = json.loads(output)
        for ws in json_output:
            if ws.get("id") == workspace:
                return int(ws.get("windows", 0))
    except subprocess.CalledProcessError as e:
        print(f"Error fetching windows in workspace {workspace}: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []

def move_window_to_workspace_and_make_master(window_address, workspace):
    """Move a window to a specified workspace and make it the master window."""
    try:
        # Move the window to the specified workspace
        subprocess.run(["hyprctl", "dispatch", "movetoworkspacesilent", f"{workspace},address:{window_address}"], check=True)
        # Wait a moment to ensure the window has been moved before attempting to make it the master
        time.sleep(0.5)  # Adjust this delay as needed
        # Switch to the workspace to ensure the next command affects the correct workspace
        subprocess.run(["hyprctl", "dispatch", "workspace", f"{workspace}"], check=True)
        # Focus the right window
        subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{window_address}"], check=True)
        time.sleep(0.5)
        # Make the window the master in its new workspace
        subprocess.run(["hyprctl", "dispatch", "layoutmsg", "swapwithmaster auto"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error processing window {window_address} for workspace {workspace}: {e}")

# def resize_window(window_address, workspace):
#     """Resize the window to a specified size."""
#     try:
#         windows_in_workspace = get_windows_in_workspace(workspace)
#         if windows_in_workspace == 2:
#             # Resize when multiple window are open
#             subprocess.run(["hyprctl", "dispatch", "resizewindowpixel", f"{size_percentage},address:{window_address}"], check=True)
#     except subprocess.CalledProcessError as e:
#         print(f"Error resizing window {window_address} in workspace {workspace}: {e}")

def main():
    # Wait for a bit to let VS Code initialize and create windows
    time.sleep(DELAY)

    # Get all windows in JSON format
    windows = get_windows()

    for window in windows:
        window_address = str(window.get("address"))
        title = window.get("title", "")
        # Check each workspace assignment condition
        for keyword, workspace in workspace_assignments.items():
            if keyword in title:  # Adjust string matching as needed
                move_window_to_workspace_and_make_master(window_address, workspace)
                # resize_window(window_address, workspace)
                break  # Move to the next window after assigning the current one

    # Switch back to the first workspace
    subprocess.run(["hyprctl", "dispatch", "workspace", "1"], check=True)

if __name__ == "__main__":
    main()
