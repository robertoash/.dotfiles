---
phase: 01-idle-detection-reliability
plan: 01
subsystem: mqtt-services
tags:
  - mqtt
  - paho-mqtt
  - reconnection
  - bug-fix
  - idle-detection
dependency_graph:
  requires:
    - paho-mqtt==1.6.x
  provides:
    - mqtt_listener.service with paho-mqtt 1.6.x compatibility
    - mqtt_reports.service with paho-mqtt 1.6.x compatibility
  affects:
    - linuxmini/systemd/user/mqtt_listener.service
    - linuxmini/systemd/user/mqtt_reports.service
tech_stack:
  added: []
  patterns:
    - paho-mqtt built-in reconnection with exponential backoff
    - Integer-based disconnect reason codes (paho-mqtt 1.6.x)
key_files:
  created: []
  modified:
    - linuxmini/scripts/mqtt/mqtt_listener.py
    - linuxmini/scripts/mqtt/mqtt_reports.py
decisions:
  - Use paho-mqtt's built-in reconnection instead of custom safe_reconnect()
  - Rely on will message for offline status instead of publishing in on_disconnect
  - Treat disconnect rc as integer for paho-mqtt 1.6.x compatibility
metrics:
  duration_seconds: 118
  tasks_completed: 2
  files_modified: 2
  commits: 2
  completed_date: 2026-02-12
---

# Phase 01 Plan 01: Fix MQTT Service Crashes Summary

Fixed critical paho-mqtt API incompatibility crashes and broken reconnection logic in mqtt_listener.py and mqtt_reports.py.

## Objective Achieved

Both MQTT scripts now work with paho-mqtt 1.6.x and use paho-mqtt's built-in reconnection mechanism instead of custom reconnection logic that fought with the library's automatic reconnection.

## Tasks Completed

### Task 1: Fix paho-mqtt compatibility and reconnection in mqtt_listener.py
**Status:** Complete
**Commit:** 2106a3c

Fixed two critical bugs:
1. Removed paho-mqtt 2.0 `DisconnectFlags` API usage that caused AttributeError on 1.6.x
2. Deleted custom `safe_reconnect()` function and related reconnection logic

Changes:
- Replaced `on_disconnect` handler to treat `rc` as integer (1.6.x behavior)
- Removed `isinstance(rc, mqtt.DisconnectFlags)` check
- Deleted `safe_reconnect()` function (lines 74-93)
- Removed `reconnecting` global variable and `RECONNECT_DELAY` constant
- Removed `reconnecting = False` from `on_connect`
- Removed offline status publishing from `on_disconnect` (will message handles this)

The service now relies on `loop_forever()` with `reconnect_delay_set(min_delay=1, max_delay=300)` for automatic reconnection with exponential backoff.

### Task 2: Fix paho-mqtt compatibility and reconnection in mqtt_reports.py
**Status:** Complete
**Commit:** 2c5dab2

Applied identical fixes to mqtt_reports.py:
1. Removed paho-mqtt 2.0 `DisconnectFlags` API usage
2. Deleted custom reconnection infrastructure

Changes:
- Replaced `on_disconnect` handler to treat `rc` as integer (1.6.x behavior)
- Removed `isinstance(rc, mqtt.DisconnectFlags)` check
- Deleted `safe_reconnect()` function (lines 122-143)
- Removed `reconnecting` global variable, `reconnect_lock`, and `RECONNECT_DELAY` constant
- Removed `reconnecting = False` from `on_connect`
- Removed `safe_reconnect()` call from `on_message` broker offline handler
- Simplified broker status change handling to just update `broker_online` flag

The service now relies on `loop_start()` with `reconnect_delay_set(min_delay=1, max_delay=300)` for automatic reconnection.

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All verification criteria passed:

1. Both Python files parse without syntax errors
2. No references to `DisconnectFlags` in either file (0 occurrences)
3. No `safe_reconnect` function in either file (0 occurrences)
4. No `reconnect_lock` in mqtt_reports.py (0 occurrences)
5. Both `on_disconnect` handlers treat `rc` as integer
6. `reconnect_delay_set` still present in both files (paho's built-in backoff)
7. `loop_forever()` still used in mqtt_listener.py
8. `loop_start()` still used in mqtt_reports.py

## Technical Details

### Before
Both scripts used paho-mqtt 2.0 API that doesn't exist in 1.6.x:
```python
if isinstance(rc, mqtt.DisconnectFlags):  # AttributeError on 1.6.x
    if rc.is_disconnect_packet_from_server:
        # ...
```

Custom reconnection logic fought with paho-mqtt's built-in reconnection:
- Manual `safe_reconnect()` calls in `on_disconnect`
- Global `reconnecting` flag and locks
- Manual `time.sleep(RECONNECT_DELAY)`

### After
Both scripts now use paho-mqtt 1.6.x compatible integer-based disconnect codes:
```python
def on_disconnect(client, userdata, rc):
    global broker_online
    broker_online = False
    if rc == 0:
        logging.info("Disconnected cleanly")
    else:
        logging.warning(f"Unexpected disconnect (rc={rc}), paho-mqtt will auto-reconnect")
```

Reconnection is fully handled by paho-mqtt:
- `reconnect_delay_set(min_delay=1, max_delay=300)` configures exponential backoff
- `loop_forever()` (listener) and `loop_start()` (reports) handle automatic reconnection
- No custom reconnection code interfering with built-in behavior

### Impact
- mqtt_listener.service should now start and stay running without crashes
- mqtt_reports.service should publish status changes without "client is not currently connected" warnings
- Both services will automatically reconnect when broker goes offline and comes back
- Reduced code by 103 lines across both files (46 from listener, 57 from reports)

## Next Steps

After this plan:
1. Apply the dotfiles changes: `cd ~/.dotfiles && python setup.py`
2. Restart both systemd services:
   ```bash
   systemctl --user restart mqtt_listener.service
   systemctl --user restart mqtt_reports.service
   ```
3. Monitor service health:
   ```bash
   systemctl --user status mqtt_listener.service
   systemctl --user status mqtt_reports.service
   ```
4. Test reconnection behavior by restarting Home Assistant and verifying services reconnect automatically

## Self-Check: PASSED

All claims verified:
- FOUND: linuxmini/scripts/mqtt/mqtt_listener.py
- FOUND: linuxmini/scripts/mqtt/mqtt_reports.py
- FOUND: commit 2106a3c
- FOUND: commit 2c5dab2
