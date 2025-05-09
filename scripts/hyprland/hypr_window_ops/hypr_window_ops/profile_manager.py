#!/usr/bin/env python3

import json
import subprocess
import time

from . import app_launcher, config, window_manager


def load_profile_data():
    """Load all profiles from the profiles JSON file."""
    if not config.PROFILE_PATH.exists():
        return {}

    return json.loads(config.PROFILE_PATH.read_text())


def save_profile_data(data):
    """Save profile data to the JSON file."""
    config.PROFILE_PATH.write_text(json.dumps(data, indent=2))


def get_current_profile():
    """Get the name of the currently active profile."""
    data = load_profile_data()
    return data.get("_current", config.DEFAULT_PROFILE)


def set_current_profile(profile_name):
    """Set the current active profile."""
    try:
        data = load_profile_data()

        # For the active profile, we'll use empty data to clearly show it's active
        if profile_name in data and profile_name != data.get("_current"):
            # Set empty win_data for the now-active profile
            data[profile_name] = {
                "staging_ws": config.DEFAULT_STAGING_WS,
                "win_data": [],
            }

        # Set the current profile marker
        data["_current"] = profile_name
        save_profile_data(data)
        print(f"✅ Set _current to '{profile_name}' in workspace_profiles.json")
    except Exception as e:
        print(f"⚠️ Failed to set _current profile: {e}")


def save_profile(profile_name):
    """Save current window layout as a named profile."""
    clients = window_manager.get_clients()
    win_data = []

    for client in clients:
        # Skip windows in any special swap workspace
        if client["workspace"]["name"].startswith("special:swap_"):
            continue
        win_data.append(
            {
                "address": client["address"],
                "class": client["class"],
                "title": client["title"],
                "target_ws": client["workspace"]["id"],
                "at": client.get("at", [0, 0]),
                "floating": client.get("floating", False),
                "monitor": client["monitor"],
            }
        )

    if not win_data:
        print(f"❌ No windows to save for profile '{profile_name}'")
        return

    # Load existing data
    data = load_profile_data()

    # Create or update profile with new format
    profile_data = {"staging_ws": config.DEFAULT_STAGING_WS, "win_data": win_data}
    data[profile_name] = profile_data

    # Save the data
    save_profile_data(data)
    print(f"✅ Saved {len(win_data)} windows to profile '{profile_name}'")


def load_profile(profile_name):
    """Load a profile by name, handling backward compatibility."""
    data = load_profile_data()

    if not data:
        print("❌ No workspace_profiles.json found.")
        return None

    if profile_name not in data:
        print(f"❌ Profile '{profile_name}' not found.")
        return None

    profile_data = data[profile_name]

    # Handle both old and new format for compatibility during transition
    if isinstance(profile_data, list):
        return {"staging_ws": config.DEFAULT_STAGING_WS, "win_data": profile_data}
    return profile_data


def build_profile(profile_name, win_data):
    """Create or update a profile with the given window data."""
    data = load_profile_data()
    data[profile_name] = win_data
    save_profile_data(data)
    print(
        f"✅ Initialized '{profile_name}' profile with {len(win_data['win_data'])} windows."
    )


def swap_to_profile(to_profile):
    """Swap from current profile to a new profile."""
    data = load_profile_data()
    from_profile = data.get("_current")

    if from_profile == to_profile:
        message = f"⚠️ Profile '{to_profile}' is already active. Nothing to do."
        print(message)
        subprocess.Popen(["dunstify", message])
        return

    print(f"🔄 Swapping from '{from_profile}' → '{to_profile}'")
    subprocess.Popen(
        ["dunstify", f"🔄 Swapping from '{from_profile}' → '{to_profile}'"]
    )

    # Save current windows to the profile we're leaving
    save_profile(from_profile)

    # Move current visible windows to the swap workspace for the profile we're leaving
    from_swap_ws = f"swap_{from_profile}"

    # Get all current windows that are not in any special workspace
    clients = window_manager.get_clients()
    visible_windows = [
        client
        for client in clients
        if not client["workspace"]["name"].startswith("special:")
    ]

    # Move all these windows to the from_swap_ws special workspace
    if visible_windows:
        print(f"Moving {len(visible_windows)} windows to special:{from_swap_ws}")
        for client in visible_windows:
            window_manager.focus_window(client["address"])
            try:
                # Move to special workspace
                subprocess.run(
                    [
                        "hyprctl",
                        "dispatch",
                        "movetoworkspacesilent",
                        f"special:{from_swap_ws}",
                    ],
                    check=True,
                )
            except Exception as e:
                print(f"⚠️ Error moving window to swap workspace: {e}")

    # Check if there are windows in the swap workspace for the target profile
    to_swap_ws = f"swap_{to_profile}"
    windows_exist_in_swap = False

    try:
        # Check workspaces to see if the special workspace exists
        result = subprocess.run(
            ["hyprctl", "workspaces", "-j"], capture_output=True, text=True, check=True
        )
        workspaces = json.loads(result.stdout)

        # Find if the special workspace exists
        special_ws = next(
            (ws for ws in workspaces if ws["name"] == f"special:{to_swap_ws}"), None
        )

        if special_ws:
            # Make the swap workspace visible
            window_manager.toggle_special_workspace(to_swap_ws)
            time.sleep(0.5)

            # Get all windows in this special workspace
            clients = window_manager.get_clients()
            swap_windows = [
                client
                for client in clients
                if client["workspace"]["name"] == f"special:{to_swap_ws}"
            ]

            if swap_windows:
                windows_exist_in_swap = True
                print(f"Found {len(swap_windows)} windows in special:{to_swap_ws}")

                # Get target profile data
                profile_data = load_profile(to_profile)
                if profile_data and profile_data.get("win_data"):
                    # Match windows by class and title
                    for win_data in profile_data["win_data"]:
                        win_class = win_data.get("class", "")
                        win_title = win_data.get("title", "")

                        # Find matching windows
                        matching_windows = [
                            window
                            for window in swap_windows
                            if (
                                win_class
                                and win_class.lower() in window["class"].lower()
                            )
                            or (
                                win_title
                                and win_title.lower() in window["title"].lower()
                            )
                        ]

                        target_ws = win_data.get("target_ws")

                        # Move matching windows to their target workspace
                        for window in matching_windows:
                            print(f"Moving {window['title']} to workspace {target_ws}")
                            window_manager.focus_window(window["address"])
                            try:
                                subprocess.run(
                                    [
                                        "hyprctl",
                                        "dispatch",
                                        "movetoworkspacesilent",
                                        str(target_ws),
                                    ],
                                    check=True,
                                )
                            except Exception as e:
                                print(f"⚠️ Error moving window to target workspace: {e}")

            # Hide the swap workspace
            window_manager.toggle_special_workspace(to_swap_ws)
    except Exception as e:
        print(f"⚠️ Error checking swap workspace: {e}")

    # If no windows exist in the swap workspace, launch apps for the target profile
    if not windows_exist_in_swap:
        print(
            f"No windows found in swap workspace. Launching apps for profile '{to_profile}'..."
        )
        subprocess.Popen(["dunstify", f"Launching apps for profile '{to_profile}'..."])

        # Launch the apps for the target profile
        app_launcher.launch_profile_apps(profile_name=to_profile)

        # Get the staging workspace for the target profile
        profile_data = config.APP_PROFILES.get(to_profile, {})
        staging_ws = profile_data.get("staging_ws", config.DEFAULT_STAGING_WS)

        # Try to move windows from staging workspace to their target workspaces
        try:
            # Switch to the staging workspace
            window_manager.switch_to_workspace(str(staging_ws))
            time.sleep(0.5)

            # Get all windows in the staging workspace
            clients = window_manager.get_clients()
            staging_windows = [
                client for client in clients if client["workspace"]["id"] == staging_ws
            ]

            # Move each window to its target workspace based on the launch_apps.json configuration
            for workspace, apps in profile_data.items():
                # Skip non-workspace keys like "staging_ws"
                if not isinstance(workspace, str) or not workspace.isdigit():
                    continue

                for app in apps:
                    # Find matching windows by app name in the title or class
                    app_name = app["name"]
                    matching_windows = [
                        window
                        for window in staging_windows
                        if app_name.lower() in window["title"].lower()
                        or app_name.lower() in window["class"].lower()
                    ]

                    for window in matching_windows:
                        print(f"Moving {window['title']} to workspace {workspace}")
                        window_manager.focus_window(window["address"])
                        try:
                            # Move to target workspace
                            subprocess.run(
                                [
                                    "hyprctl",
                                    "dispatch",
                                    "movetoworkspacesilent",
                                    workspace,
                                ],
                                check=True,
                            )
                        except Exception as e:
                            print(f"⚠️ Error moving window to target workspace: {e}")
        except Exception as e:
            print(f"⚠️ Error moving windows to target workspaces: {e}")

    # Return to workspace 1 for primary monitor and 11 for secondary monitor
    window_manager.switch_to_workspace("11")
    time.sleep(0.3)
    window_manager.switch_to_workspace("1")

    # Set the current profile (this will create empty data for the active profile)
    set_current_profile(to_profile)
    print(f"✅ Restored profile '{to_profile}'")
