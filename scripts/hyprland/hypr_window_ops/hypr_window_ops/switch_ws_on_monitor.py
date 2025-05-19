#!/usr/bin/env python3

import sys

from . import window_manager


def get_focused_monitor():
    """Return the id of the currently focused monitor (as int)."""
    monitors = window_manager.run_hyprctl(["monitors", "-j"])
    print(f"[DEBUG] Monitors: {monitors}")
    if not monitors:
        print("No monitors found.")
        return None
    for mon in monitors:
        if mon.get("focused"):
            print(f"[DEBUG] Focused monitor: {mon}")
            return int(mon["id"])
    print("No focused monitor found.")
    return None


def get_workspaces_on_monitor(monitor_id):
    print(f"[DEBUG] Entered get_workspaces_on_monitor with monitor_id={monitor_id}")
    try:
        print("[DEBUG] Calling window_manager.get_workspaces()...")
        workspaces = window_manager.run_hyprctl(["workspaces", "-j"])
        print(f"[DEBUG] window_manager.get_workspaces() returned: {workspaces}")
        print(f"[DEBUG] Type of workspaces: {type(workspaces)}")
    except Exception as e:
        print(f"[ERROR] Exception while fetching workspaces: {e}")
        return []
    if not workspaces:
        print("[DEBUG] No workspaces returned from get_workspaces()!")
        return []
    ws_on_monitor = [
        ws for ws in workspaces if int(ws.get("monitorID", -1)) == int(monitor_id)
    ]
    print(f"[DEBUG] Workspaces on monitor {monitor_id}: {ws_on_monitor}")
    # Ignore negative workspace ids
    ws_on_monitor = [ws for ws in ws_on_monitor if ws.get("id") > 0]
    print(f"[DEBUG] Workspaces on monitor {monitor_id} (id > 0): {ws_on_monitor}")
    # Sort by workspace id (numeric)
    ws_on_monitor.sort(key=lambda ws: ws.get("id", 0))
    print(f"[DEBUG] Sorted workspaces on monitor {monitor_id}: {ws_on_monitor}")
    return ws_on_monitor


def switch_to_nth_workspace_on_focused_monitor(n):
    monitor = get_focused_monitor()
    print(f"[DEBUG] Using monitor id: {monitor}")
    if monitor is None:
        print("No focused monitor found.")
        return 1
    ws_list = get_workspaces_on_monitor(monitor)
    print(f"[DEBUG] Workspaces on monitor {monitor}: {ws_list}")
    if not ws_list:
        print(f"No workspaces found on monitor {monitor}.")
        return 1
    if n < 1 or n > len(ws_list):
        print(f"Workspace {n} does not exist on monitor {monitor}.")
        return 1
    ws_id = ws_list[n - 1]["id"]
    print(
        f"[DEBUG] Switching to workspace id: {ws_id} (index {n-1}) on monitor {monitor}"
    )
    window_manager.switch_to_workspace(ws_id)
    return 0


def switch_to_next_workspace_on_focused_monitor():
    monitor = get_focused_monitor()
    print(f"[DEBUG] Using monitor id: {monitor}")
    if monitor is None:
        print("No focused monitor found.")
        return 1
    ws_list = get_workspaces_on_monitor(monitor)
    print(f"[DEBUG] Workspaces on monitor {monitor}: {ws_list}")
    # Determine the workspace id range for this monitor
    if monitor == 0:
        ws_range = range(1, 11)
    elif monitor == 1:
        ws_range = range(11, 21)
    else:
        ws_range = range(21, 1000)  # Arbitrary upper bound for extra monitors
    used_ids = {ws["id"] for ws in ws_list}
    next_ws_id = None
    for ws_id in ws_range:
        if ws_id not in used_ids:
            next_ws_id = ws_id
            break
    if next_ws_id is None:
        # If all in range are used, pick the next available after the range (for monitor 0)
        if monitor == 0:
            next_ws_id = max(used_ids | set([10])) + 1
        else:
            # For other monitors, just pick the next after the range
            next_ws_id = ws_range.stop
    print(f"[DEBUG] Switching to next workspace id: {next_ws_id} on monitor {monitor}")
    window_manager.switch_to_workspace(next_ws_id)
    return 0


def main():
    if len(sys.argv) == 2:
        try:
            n = int(sys.argv[1])
        except ValueError:
            print("N must be an integer.")
            return 1
        return switch_to_nth_workspace_on_focused_monitor(n)
    elif len(sys.argv) == 3 and sys.argv[1] == "next":
        return switch_to_next_workspace_on_focused_monitor()
    else:
        print("Usage: switch_ws_on_monitor.py N | next")
        return 1


if __name__ == "__main__":
    sys.exit(main())
