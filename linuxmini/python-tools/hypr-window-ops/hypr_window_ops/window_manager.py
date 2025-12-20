#!/usr/bin/env python3

import json
import subprocess
import time

from . import config


def run_hyprctl(command):
    """Run a hyprctl command and return the parsed JSON output."""
    result = subprocess.run(["hyprctl"] + command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {' '.join(command)}: {result.stderr}")
        return None
    return json.loads(result.stdout)


def run_hyprctl_command(command):
    """Run a hyprctl command that doesn't return JSON (like dispatch, setprop)."""
    # Debug output
    if "movewindowpixel" in command:
        print(f"Debug: hyprctl command: {['hyprctl'] + command}")
    result = subprocess.run(["hyprctl"] + command, capture_output=True, text=True)
    if "movewindowpixel" in command:
        print(f"Debug: result stdout: {result.stdout}")
        print(f"Debug: result stderr: {result.stderr}")
    return result.returncode == 0


def get_hyprland_gaps_out():
    """
    Get the gaps_out value from Hyprland using hyprctl.

    Returns:
        int: The gaps_out value (default: 0 if not found or on error)
    """
    try:
        result = run_hyprctl(["getoption", "general:gaps_out", "-j"])
        if result and "custom" in result:
            # gaps_out can be "20 20 20 20" (top right bottom left)
            # or just "20" - we'll take the first value
            gaps_str = result["custom"]
            first_value = gaps_str.split()[0]
            return int(first_value)
        return 0
    except Exception as e:
        print(f"Warning: Could not read gaps_out: {e}")
        return 0


def get_clients():
    """Get all clients/windows."""
    return run_hyprctl(["clients", "-j"])


def get_workspaces():
    """Get all workspaces."""
    return run_hyprctl(["workspaces", "-j"])


def get_active_workspace_id():
    """Get the ID of the active workspace."""
    return run_hyprctl(["activewindow", "-j"])["workspace"]["id"]


def get_monitor_for_ws(ws_id):
    """Get the monitor name for a workspace ID."""
    workspaces = get_workspaces()
    return next((ws["monitor"] for ws in workspaces if ws["id"] == ws_id), None)


def get_target_window_with_focus(relative_floating=False, for_toggle_floating_activation=False):
    """
    Get the target window and focus it if needed (when using smart targeting).

    Args:
        relative_floating: Enable smart targeting for floating windows
        for_toggle_floating_activation: True when toggle-floating is making a tiled window floating

    Returns:
        tuple: (window_info dict, original_active_address str or None)
            - window_info: The window to operate on
            - original_active_address: Address to restore focus to (None if no focus change needed)
    """
    if not relative_floating:
        return run_hyprctl(["activewindow", "-j"]), None

    # Get original active window before smart targeting
    original_active = run_hyprctl(["activewindow", "-j"])
    original_address = original_active.get("address") if original_active else None

    target = get_target_floating_window(for_toggle_floating_activation)

    if target is None:
        return original_active, None

    # Smart target found - focus it
    focus_window(target["address"])
    return target, original_address


def get_target_floating_window(for_toggle_floating_activation=False):
    """
    Determine which window to target for floating window operations.

    Args:
        for_toggle_floating_activation: True when toggle-floating is being used
            to make a tiled window floating (affects targeting logic)

    Returns:
        dict or None: Window info dict for the target window, or None if should
                      use active window (caller handles getting active window)

    Logic:
        1. Get active window - if floating, return None (caller uses active)
        2. Get visible workspaces (one per monitor)
        3. Get all floating windows in visible workspaces
        4. Determine current monitor from active window
        5. Count total floating and floating on current monitor
        6. Apply targeting rules based on count
    """
    # Step 1: Get active window
    active_window = run_hyprctl(["activewindow", "-j"])
    if not active_window or "address" not in active_window:
        return None  # Fallback to active window (will be handled by caller)

    # Early exit: if active is floating, use it
    if active_window.get("floating", False):
        return None  # Signal to use active window

    # Step 2: Get visible workspaces
    monitors = run_hyprctl(["monitors", "-j"])
    if not monitors:
        return None

    visible_workspace_ids = {
        mon["activeWorkspace"]["id"]
        for mon in monitors
        if "activeWorkspace" in mon
    }

    # Step 3: Get all clients and filter for floating in visible workspaces
    all_clients = get_clients()
    if not all_clients:
        return None

    floating_in_visible = [
        client
        for client in all_clients
        if client.get("floating", False)
        and client.get("workspace", {}).get("id") in visible_workspace_ids
    ]

    # Step 4: Determine current monitor
    current_monitor = active_window.get("monitor")
    if current_monitor is None:
        # Fallback: find focused monitor
        focused_mon = next((m for m in monitors if m.get("focused")), None)
        current_monitor = focused_mon["id"] if focused_mon else 0

    # Step 5: Count floating windows
    total_floating = len(floating_in_visible)
    floating_on_current = [
        w for w in floating_in_visible if w.get("monitor") == current_monitor
    ]
    count_on_current = len(floating_on_current)

    # Step 6: Apply targeting rules
    # Exception for toggle-floating activation: always use active window
    if for_toggle_floating_activation:
        return None

    # Exactly 1 floating total
    if total_floating == 1:
        return floating_in_visible[0]

    # Exactly 1 floating on current monitor
    if count_on_current == 1:
        return floating_on_current[0]

    # Default: use active window
    return None


def get_windows_in_workspace(workspace_id):
    """Get all window addresses in a workspace."""
    clients = get_clients()
    return [
        client["address"]
        for client in clients
        if client["workspace"]["id"] == workspace_id
    ]


def get_workspace_id(workspace_name):
    """Get workspace ID from workspace name."""
    workspaces = get_workspaces()
    for ws in workspaces:
        if ws["name"] == workspace_name or ws["name"] == f"special:{workspace_name}":
            return ws["id"]
    return None


def get_window_addresses():
    """Retrieve the set of current window addresses."""
    try:
        clients = get_clients()
        return {client["address"] for client in clients}
    except Exception:
        return set()


def get_master_window_address(workspace_id):
    """Get the address of the master window for a given workspace."""
    try:
        clients = get_clients()
        workspace_clients = [
            c for c in clients if c.get("workspace", {}).get("id") == int(workspace_id)
        ]

        if not workspace_clients:
            return None

        # Find the master window: sort by at[0] first, then at[1] as a tiebreaker
        master_window = min(
            workspace_clients,
            key=lambda w: (
                w.get("at", [float("inf"), float("inf")])[0],
                w.get("at", [float("inf"), float("inf")])[1],
            ),
        )

        return master_window.get("address")

    except Exception as e:
        print(f"Error checking master window: {e}")
        return None


def is_window_master(window_address, workspace):
    """Check if the given window is the master window."""
    master_window = get_master_window_address(workspace)
    if not master_window:
        return False
    return master_window == window_address


def wait_for_window(existing_windows, timeout=None):
    """Wait for a new window to appear, up to `timeout` seconds."""
    if timeout is None:
        timeout = config.MAX_WAIT_FOR_WINDOW
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_windows = get_window_addresses()
        new_windows = current_windows - existing_windows
        if new_windows:
            # Get the first window address
            return next(iter(new_windows))
        time.sleep(0.1)  # Check every 100ms
    print("Warning: Window did not appear within timeout.")
    return None


def switch_to_workspace(workspace):
    """Switch to a specified workspace."""
    run_hyprctl_command(["dispatch", "workspace", f"{workspace}"])


def focus_window(address):
    """Focus a window by address."""
    run_hyprctl_command(["dispatch", "focuswindow", f"address:{address}"])


def toggle_special_workspace(workspace_name):
    """Toggle a special workspace visibility."""
    run_hyprctl_command(["dispatch", "togglespecialworkspace", workspace_name])


def move_window_to_workspace(window_address, workspace, silent=True):
    """Move a window to a specified workspace."""
    workspace_str = workspace
    cmd = "movetoworkspacesilent" if silent else "movetoworkspace"
    run_hyprctl_command(
        ["dispatch", f"{cmd}", f"{workspace_str},address:{window_address}"]
    )


def get_monitor_transform_map():
    """Get a mapping of monitor names to transform values."""
    return {m["name"]: m.get("transform", 0) for m in run_hyprctl(["monitors", "-j"])}


def reorder_windows_by_at(layout):
    """Reorder windows based on their position coordinates."""
    transform_map = get_monitor_transform_map()
    grouped = {}
    for win in layout:
        ws_id = win["target_ws"]
        grouped.setdefault(ws_id, []).append(win)

    for ws_id, windows in grouped.items():
        monitor = next((w.get("monitor") for w in windows if w.get("monitor")), None)
        if not monitor:
            continue
        transform = transform_map.get(monitor, 0)
        is_vertical = transform in [1, 3]
        sorted_windows = sorted(
            windows,
            key=lambda w: (
                (w["at"][1], w["at"][0]) if is_vertical else (w["at"][0], w["at"][1])
            ),
        )

        for i, win in enumerate(sorted_windows):
            focus_window(win["address"])
            for _ in range(i):
                run_hyprctl_command(["dispatch", "layoutmsg", "swapprev"])


def get_target_id(target_workspace, target_is_special):
    """Convert a workspace name/id to a numeric ID."""
    return (
        get_workspace_id(target_workspace)
        if target_is_special
        else int(target_workspace)
    )


def move_windows(
    window_addresses,
    source_id,
    target_id,
    target_workspace,
    target_is_special=False,
    layout=None,
):
    """Move a group of windows from one workspace to another and apply layout."""
    target_master = get_master_window_address(target_id) if target_id else None
    if not target_master and source_id:
        target_master = get_master_window_address(source_id)

    if target_id != source_id:
        for address in window_addresses:
            if target_is_special:
                focus_window(address)
                toggle_special_workspace(target_workspace)
            else:
                move_window_to_workspace(address, target_workspace)

        if layout is None:
            # Reconstruct layout from current clients
            clients = get_clients()
            workspaces = get_workspaces()

            # Resolve target workspace ID and monitor
            ws_id = target_id
            monitor = next(
                (ws["monitor"] for ws in workspaces if ws["id"] == ws_id), None
            )

            inferred_layout = [
                {
                    "address": c["address"],
                    "at": c.get("at", [0, 0]),
                    "target_ws": c["workspace"]["id"],
                    "monitor": monitor,
                }
                for c in clients
                if c["workspace"]["id"] == ws_id
            ]

            reorder_windows_by_at(inferred_layout)
        else:
            reorder_windows_by_at(layout)
    else:
        print("Source and target workspaces are the same. No action taken.")

    return source_id, target_id, target_workspace, target_is_special


def final_focus(source_id, target_id, target_workspace, target_is_special):
    """Set final focus after moving windows."""
    if target_id is None:
        target_id = get_target_id(target_workspace, target_is_special)
    source_is_special = source_id < 0
    should_focus_source = not source_is_special and target_is_special

    # First switch to appropriate workspace
    switch_to_workspace(source_id if should_focus_source else target_id)

    # Toggle special workspace if needed
    if should_focus_source and target_is_special:
        toggle_special_workspace(target_workspace)


def move_all_workspace_windows(source_id, target_workspace):
    """Move all windows from source workspace to target workspace."""
    target_is_special = not str(target_workspace).isdigit()
    target_id = get_target_id(target_workspace, target_is_special)

    if target_id is not None and source_id == target_id:
        print("Source and target workspaces are the same. No action taken.")
        return

    window_addresses = get_windows_in_workspace(source_id)
    if not window_addresses:
        print(f"No windows found in workspace {source_id}.")
        return

    return move_windows(
        window_addresses,
        source_id,
        target_id,
        target_workspace=target_workspace,
        target_is_special=target_is_special,
        layout=None,
    )
