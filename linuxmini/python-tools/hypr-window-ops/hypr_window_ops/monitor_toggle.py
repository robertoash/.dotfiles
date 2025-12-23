#!/usr/bin/env python3

import json
from pathlib import Path

from . import window_manager as wm


STATE_FILE = Path.home() / ".cache" / "hyprland" / "last_active_windows.json"


def load_state():
    """Load the last active windows state from cache."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_state(state):
    """Save the last active windows state to cache."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_windows_in_workspace(workspace_id):
    """Get all windows in a specific workspace."""
    clients = wm.get_clients()
    return [c for c in clients if c.get("workspace", {}).get("id") == workspace_id]


def toggle_active_monitor():
    """
    Toggle focus to the next monitor and restore last active window in target workspace.

    This function:
    1. Saves the current active window for the current workspace (including special workspaces)
    2. Switches to the next monitor
    3. Restores the last active window in the target monitor's workspace
    """
    monitors = wm.run_hyprctl(["monitors", "-j"])
    if not monitors:
        return 1

    current_window = wm.run_hyprctl(["activewindow", "-j"])

    # Save current active window to state
    if current_window and "workspace" in current_window:
        workspace_id = current_window["workspace"]["id"]
        window_address = current_window.get("address")

        if window_address:
            state = load_state()
            state[str(workspace_id)] = window_address
            save_state(state)

    # Find next monitor
    focused_index = next((i for i, m in enumerate(monitors) if m.get("focused")), None)
    if focused_index is None:
        return 1

    next_index = (focused_index + 1) % len(monitors)
    next_monitor = monitors[next_index]

    # Check if a special workspace is visible on target monitor, use that instead of activeWorkspace
    special_ws = next_monitor.get("specialWorkspace", {})
    if special_ws.get("id", 0) != 0:
        target_workspace_id = special_ws.get("id")
    else:
        target_workspace_id = next_monitor["activeWorkspace"]["id"]

    # Switch to the monitor first
    wm.run_hyprctl_command(["dispatch", "focusmonitor", next_monitor["name"]])

    # Try to restore last active window in target workspace
    state = load_state()
    last_window_address = state.get(str(target_workspace_id))

    if last_window_address:
        # Check if the window still exists in that workspace
        windows = get_windows_in_workspace(target_workspace_id)
        if any(w.get("address") == last_window_address for w in windows):
            # Focus the last active window
            wm.focus_window(last_window_address)

    return 0
