#!/usr/bin/env python3

import subprocess
import time
import json

DELAY = 120  # Initial delay before starting the script

window_class_combinations = {
    "75% 100%": [
        ["code-insiders-url-handler", "foot"]
    ],
    "70% 100%": [
        ["vivaldi-stable", "foot"],
        ["slack", "obsidian"],
    ]
    # Add more combinations as needed
}
previous_workspace_states = {}


def check_combination_exists(window_classes, combinations) -> str or None:
    # Convert all window classes to lower case for case-insensitive comparison
    window_classes_set = set([cls.lower() for cls in window_classes])
    for combo, combination_groups in combinations.items():
        for combination in combination_groups:
            # Similarly, convert each combination group to lower case before comparison
            combination_set = set([cls.lower() for cls in combination])
            if window_classes_set == combination_set and len(window_classes) == len(combination):
                return combo
    return None

#*********

def get_all_clients_info() -> list[dict]:
    try:
        output = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, check=True, text=True)
        return json.loads(output.stdout)
    except Exception as e:
        print(f"Error getting all clients info: {e}")
        return []

def get_all_workspaces_info() -> list[dict]:
    try:
        output = subprocess.run(["hyprctl", "workspaces", "-j"], capture_output=True, check=True, text=True)
        return json.loads(output.stdout)
    except Exception as e:
        print(f"Error getting all workspaces info: {e}")
        return []

def get_all_monitor_sizes() -> dict:
    try:
        output = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, check=True, text=True)
        monitors_info = json.loads(output.stdout)
        return {monitor["id"]: [monitor["width"], monitor["height"]] for monitor in monitors_info}
    except Exception as e:
        print(f"Error getting all monitor orientations: {e}")
        return {}

def get_all_monitor_orientations() -> dict:
    try:
        output = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, check=True, text=True)
        monitors_info = json.loads(output.stdout)
        return {monitor["id"]: monitor["transform"] for monitor in monitors_info}
    except Exception as e:
        print(f"Error getting all monitor orientations: {e}")
        return {}

def get_workspace_window_count() -> dict:
    try:
        output = subprocess.run(["hyprctl", "workspaces", "-j"], capture_output=True, check=True, text=True)
        workspaces_info = json.loads(output.stdout)
        return {workspace["id"]: workspace["windows"] for workspace in workspaces_info}
    except Exception as e:
        print(f"Error getting workspace window count: {e}")
        return {}

#*********

def get_all_master_addresses(clients_info, workspaces_info, monitor_orientations) -> dict:
    try:
        master_addresses = {}

        for workspace in workspaces_info:
            workspace_id = workspace["id"]
            monitor_id = workspace["monitorID"]
            workspace_orientation = monitor_orientations[monitor_id]

            # If the workspace is in a vertical monitor, compare the y coordinate instead
            if workspace_orientation in [1, 3]:
                master_client = min([client for client in clients_info if client['workspace']['id'] == workspace_id], key=lambda client: client["at"][1])
            else:
                master_client = min([client for client in clients_info if client['workspace']['id'] == workspace_id], key=lambda client: client["at"][0])

            master_addresses[workspace_id] = master_client["address"]

        return master_addresses
    except Exception as e:
        print(f"Error getting all master window addresses: {e}")
        return {}

def get_window_classes(clients_info, workspaces_info, ws_id) -> list[str]:
    try:
        for workspace in workspaces_info:
            return [client["class"] for client in clients_info if client["workspace"]["id"] == ws_id]
    except Exception as e:
        print(f"Error getting window classes for workspace {ws_id}: {e}")
        return []


previous_workspace_ratios = {}
previous_workspace_window_count = {}

def main():
    global previous_workspace_ratios, previous_workspace_window_count
    time.sleep(DELAY)  # Initial delay on boot

    while True:
        clients_info = get_all_clients_info()
        workspaces_info = get_all_workspaces_info()
        monitor_sizes = get_all_monitor_sizes()
        monitor_orientations = get_all_monitor_orientations()
        workspace_window_counts = get_workspace_window_count()

        master_window_addresses = get_all_master_addresses(clients_info, workspaces_info, monitor_orientations)

        for workspace in workspaces_info:
            ws_id = workspace["id"]

            # Fetch current window classes and check if a valid combination exists
            window_classes = get_window_classes(clients_info, workspaces_info, ws_id)
            found_combo = check_combination_exists(window_classes, window_class_combinations)

            current_window_count = workspace_window_counts[ws_id]
            # Retrieve previous window count
            prev_window_count = previous_workspace_window_count.get(ws_id, {}).get('window_count', 0)

            if found_combo and current_window_count > prev_window_count:

                # Split the found combo into x and y ratios
                x_ratio, y_ratio = found_combo.split(" ")
                # Remove the % in each element and divide by 100
                x_ratio = int(x_ratio.strip("%")) / 100
                y_ratio = int(y_ratio.strip("%")) / 100

                # Get the monitor size and calculate the exact pixel size for the window
                monitor_size = monitor_sizes[workspace["monitorID"]]
                exact_x = int(monitor_size[0] * x_ratio)
                exact_y = int(monitor_size[1] * y_ratio)

                # Account for monitor orientation
                monitor_orientation = monitor_orientations[workspace["monitorID"]]
                if monitor_orientation in [1, 3]:
                    exact_x, exact_y = exact_y, exact_x

                resize_params = f"exact {exact_x} {exact_y}"

                if master_window_addresses[ws_id]:
                    master_address = master_window_addresses[ws_id]
                    # Execute the resize command only if a valid ratio is found
                    subprocess.run(["hyprctl", "dispatch", "resizewindowpixel", f"{resize_params},address:{master_address}"], check=True)

                    # Debug output
                    #print('vertical' if exact_x < exact_y else 'horizontal')
                    #print(master_window_addresses)
                    #print(master_address)
                    #print(f'hyprctl dispatch resizewindowpixel {resize_params},address:{master_address}')
                    #print(f"Adjusted windows in workspace {ws_id} to exact {found_combo}")
                # Update the ratio for this workspace
                previous_workspace_ratios[ws_id] = {'ratio': found_combo}
            else:
                # Clear the ratio information if no valid combination is found
                previous_workspace_ratios.pop(ws_id, None)

            # Always update the window count for tracking
            previous_workspace_window_count[ws_id] = {'window_count': current_window_count}

        time.sleep(1)  # Delay before checking again

if __name__ == "__main__":
    main()
