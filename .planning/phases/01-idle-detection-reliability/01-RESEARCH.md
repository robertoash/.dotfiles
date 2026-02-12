# Phase 1: Idle Detection Reliability - Research

**Researched:** 2026-02-12
**Domain:** Linux idle detection system with Home Assistant integration
**Confidence:** HIGH

## Summary

The idle detection system on linuxmini is a multi-layered architecture combining hypridle (Hyprland's idle daemon), systemd services, MQTT communication with Home Assistant, and custom Python scripts. The system reports user activity status to Home Assistant, which feeds back presence information to control display power management and screen locking.

The research uncovered several critical issues:

1. **CRITICAL BUG**: mqtt_listener.service is crashed due to paho-mqtt API incompatibility. The code uses `mqtt.DisconnectFlags` which doesn't exist in paho-mqtt 1.6.1 (only available in 2.0+). This is the root cause of the reported service failures.

2. **MQTT connectivity issues**: mqtt_reports.service shows repeated "client is not currently connected" warnings, indicating reconnection logic failures.

3. **Architecture complexity**: The system has multiple interdependent components (6+ systemd services, 15+ Python scripts) creating potential failure cascades.

**Primary recommendation:** Fix the paho-mqtt compatibility bug immediately, audit all MQTT reconnection logic, add comprehensive health monitoring, and implement proper systemd restart policies.

## System Architecture Analysis

### Component Inventory

**Core Services:**
- `hypridle.service` - Hyprland's idle daemon (watches for user inactivity)
- `mqtt_reports.service` - Publishes local status to MQTT broker
- `mqtt_listener.service` - Subscribes to Home Assistant topics (CURRENTLY CRASHED)
- `idle-status.service` - Updates Waybar with idle detection status
- `in-office-monitor.service` - Watches HA presence sensor and controls DPMS
- `in-office-status.service` - Updates Waybar with office presence status

**Status Files (in /tmp/mqtt/):**
- `linux_mini_status` - User activity state (active/inactive)
- `idle_detection_status` - Detection phase (inactive/in_progress)
- `in_office_status` - Office presence from HA (on/off)
- `linux_webcam_status` - Webcam usage indicator
- `manual_override_status` - Manual idle override state

**Key Scripts:**
- `activity_status_reporter.py` - Updates status files based on idle events
- `idle_simple_resume.py` - Cleanup on user return from idle
- `in_office_monitor.py` - Continuous monitoring of HA presence sensor
- `waybar_idle_status.py` - UI status indicator logic
- `config.py` - Centralized configuration for all scripts

**Home Assistant Integration:**
- MQTT binary sensors: `linux_mini_active`, `linux_webcam_active`, `linux_idle_manual_override`
- MQTT topic subscribed: `homeassistant/binary_sensor.rob_in_office/status`
- HA automations respond to `in_office` status changes

### Data Flow

1. **Idle Detection Flow:**
   - hypridle detects 60s inactivity → calls `activity_status_reporter.py --inactive`
   - Reporter writes "inactive" to `linux_mini_status` file
   - mqtt_reports watches file → publishes to MQTT broker
   - Home Assistant receives status update

2. **Presence Feedback Flow:**
   - Home Assistant calculates `rob_in_office` based on multiple sensors
   - mqtt_listener subscribes to HA topic → writes to `in_office_status` file
   - in_office_monitor.py watches file → triggers lock/DPMS actions
   - Status changes reflected in Waybar UI

3. **Resume Flow:**
   - User activity detected → hypridle calls `idle_simple_resume.py`
   - Script calls `activity_status_reporter.py --active`
   - Status files updated → MQTT published → HA updated → monitor adjusts

## Critical Bugs Discovered

### Bug #1: MQTT Listener Service Crash (CRITICAL)

**Location:** `/home/rash/.dotfiles/linuxmini/scripts/mqtt/mqtt_listener.py:140`

**Error:**
```
AttributeError: module 'paho.mqtt.client' has no attribute 'DisconnectFlags'
```

**Root Cause:** Code uses paho-mqtt 2.0 API (`mqtt.DisconnectFlags`) but system has paho-mqtt 1.6.1 installed.

**Impact:** mqtt_listener.service has been dead since Feb 12 03:49:58. The system cannot receive presence updates from Home Assistant, breaking the feedback loop that prevents unwanted locking.

**Lines 136-147:**
```python
def on_disconnect(client, userdata, rc):
    global broker_online
    logging.debug(f"on_disconnect called with rc={rc}")

    if isinstance(rc, mqtt.DisconnectFlags):  # ← CRASHES HERE
        if rc.is_disconnect_packet_from_server:
            logging.warning("Disconnected: Server might be down.")
            broker_online = False
```

**Fix Strategy:** Revert to paho-mqtt 1.6.1 compatible API. In version 1.x, `on_disconnect` callback signature is `on_disconnect(client, userdata, rc)` where `rc` is an integer return code, not a DisconnectFlags object.

### Bug #2: MQTT Reports Reconnection Failures

**Location:** `/home/rash/.dotfiles/linuxmini/scripts/mqtt/mqtt_reports.py`

**Symptoms:**
```
2026-02-12 22:15:40 [WARNING] Failed to publish scripts/linux_mini/status: The client is not currently connected.
```

**Analysis:** While mqtt_reports.service is running, it's repeatedly failing to publish because:
1. Connection drops (common with network/broker issues)
2. Reconnection logic runs but doesn't properly wait for connection establishment
3. File changes trigger publish attempts before connection is ready

**Current Reconnection Logic Issues:**
- Uses global `reconnecting` flag but doesn't prevent concurrent reconnection attempts robustly
- Thread safety issues: `reconnect_lock` exists but watchdog thread can still trigger publishes during reconnection
- `time.sleep(RECONNECT_DELAY)` doesn't guarantee connection establishment
- No exponential backoff for repeated failures

### Bug #3: systemd Restart Policy Gaps

**Current Configuration:**
```ini
[Service]
Restart=on-failure
RestartSec=5
```

**Issues:**
1. No `StartLimitIntervalSec` or `StartLimitBurst` - defaults can cause service to give up after too few retries
2. `RestartSec=5` is static - no backoff for persistent failures
3. No `RestartSteps` or `RestartMaxDelaySec` for exponential backoff
4. Services lack dependency ordering - can start in wrong order after boot

## Standard Stack

### Core Technologies

| Technology | Version | Purpose | Status |
|------------|---------|---------|--------|
| hypridle | Latest (Hyprland ecosystem) | Idle detection daemon | ✅ Working |
| paho-mqtt | 1.6.1 | MQTT client library | ⚠️ Version mismatch |
| systemd | System default | Service management | ⚠️ Needs tuning |
| watchdog | Python library | File monitoring | ✅ Working |
| Home Assistant | User's instance | Central automation hub | ✅ Working |

### Supporting Tools

| Tool | Purpose | Used For |
|------|---------|----------|
| hyprlock | Screen locker | Triggered by idle/presence |
| hyprctl | Hyprland IPC | DPMS control |
| watchexec | File watcher | Waybar status updates |
| jq | JSON processor | Waybar status parsing |

### Python Dependencies

**Required packages:**
- `paho-mqtt>=1.6.1,<2.0` (currently 1.6.1, compatible)
- `watchdog` (file system monitoring)

**Recommendation:** Pin paho-mqtt to 1.6.x range until migration to 2.0 API is completed.

## Architecture Patterns

### Pattern 1: Status File Communication

**What:** Use temporary files in `/tmp/mqtt/` as IPC between services

**Pros:**
- Language-agnostic
- Easy to debug (just cat the file)
- Survives service restarts
- No network dependencies

**Cons:**
- Race conditions possible
- No built-in change notification
- Files lost on reboot
- Manual cleanup required

**Current Implementation:**
```python
# Writer (activity_status_reporter.py)
status_file = Path("/tmp/mqtt/linux_mini_status")
status_file.write_text("active")

# Reader (in_office_monitor.py)
status = status_file.read_text().strip()
```

**Best Practice:** Use watchdog library for change detection rather than polling, ensure atomic writes, validate content before reading.

### Pattern 2: MQTT Bridge Architecture

**What:** Local status files → mqtt_reports → MQTT broker → Home Assistant → mqtt_listener → local status files

**Why:** Decouples local idle detection from HA availability. System can function (lock screen, control DPMS) even if MQTT/HA is down.

**Implementation Details:**
```python
# mqtt_reports: file watcher + MQTT publisher
observer = Observer()
observer.schedule(FileChangeHandler(mqtt_client), path="/tmp/mqtt")

# mqtt_listener: MQTT subscriber + file writer
def on_message(client, userdata, message):
    file_path = topic_to_file[message.topic]
    write_status_file(file_path, message.payload.decode())
```

**Critical Requirement:** Both services MUST have robust reconnection logic since MQTT broker can go offline.

### Pattern 3: Hypridle Listener Configuration

**What:** Progressive timeout strategy with on-timeout/on-resume pairs

**Current Configuration:**
```conf
# Report inactive after 60s
listener {
    timeout = 60
    on-timeout = activity_status_reporter.py --inactive
    on-resume = idle_simple_resume.py
}

# Fallback lock after 30 minutes
listener {
    timeout = 1800
    on-timeout = bash -c 'pidof hyprlock || hyprlock'
    on-resume = idle_simple_resume.py
}

# Turn off displays 30s after lock
listener {
    timeout = 1830
    on-timeout = hyprctl dispatch dpms off
    on-resume = idle_simple_resume.py
}
```

**Best Practices from Hypridle Documentation:**
- Use `pidof hyprlock || hyprlock` to prevent multiple instances
- Set `ignore_dbus_inhibit = false` to respect app inhibit requests (firefox, steam)
- Use `before_sleep_cmd = loginctl lock-session` for suspend integration
- Use `after_sleep_cmd = hyprctl dispatch dpms on` to avoid double-keypress after wake

**Source:** [hypridle documentation](https://wiki.hypr.land/Hypr-Ecosystem/hypridle/)

### Pattern 4: Systemd Service Dependencies

**Current Approach:** Services use `After=` but not `Requires=` or `BindsTo=`

**Issue:** Services can start in any order or run independently even when dependencies fail.

**Better Pattern:**
```ini
[Unit]
After=network.target graphical-session.target
Requires=network.target
PartOf=graphical-session.target

[Service]
Type=simple
Restart=on-failure
RestartSec=5s
StartLimitIntervalSec=60
StartLimitBurst=5
```

**For MQTT services specifically:**
```ini
# mqtt_listener should require mqtt_reports to be healthy
After=mqtt_reports.service
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MQTT reconnection | Custom retry loops | paho-mqtt's built-in `loop_forever()` or `loop_start()` | Built-in methods handle reconnection automatically with proper state management |
| File watching | `while True: check_file()` loops | watchdog library | Efficient inotify-based watching, prevents polling overhead |
| Logging | Custom file writing | Python logging module | Thread-safe, configurable, handles rotation |
| Configuration | Individual script constants | Centralized config.py | Single source of truth prevents drift |

**Current System Status:** ✅ Uses watchdog, ✅ Uses logging module, ✅ Has config.py, ⚠️ MQTT reconnection needs fixing

## Common Pitfalls

### Pitfall 1: MQTT Version Compatibility

**What goes wrong:** Code written for paho-mqtt 2.0 breaks on 1.6.x (or vice versa)

**Why it happens:** Major API changes in 2.0:
- `on_disconnect` callback signature changed
- `DisconnectFlags` class added
- `CallbackAPIVersion` parameter required for Client()

**How to avoid:**
1. Pin paho-mqtt version in requirements or system package manager
2. Check installed version at runtime if supporting multiple versions
3. Use version-specific code paths:
```python
import paho.mqtt.client as mqtt
MQTT_V2 = hasattr(mqtt, 'CallbackAPIVersion')

if MQTT_V2:
    def on_disconnect(client, userdata, flags, reason_code, properties):
        if flags.is_disconnect_packet_from_server:
            # Server initiated disconnect
else:
    def on_disconnect(client, userdata, rc):
        if rc != 0:
            # Unexpected disconnect
```

**Warning signs:**
- AttributeError with mqtt module attributes
- Service exits with "module has no attribute X"
- Callbacks never fire or fire with wrong number of arguments

**Sources:**
- [Paho-MQTT 2.0 Migration Guide](https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html)
- [Paho-MQTT Version 2 Changes](http://www.steves-internet-guide.com/paho-mqtt-python-client-version-2/)

### Pitfall 2: MQTT Connection State Management

**What goes wrong:** Publishing to disconnected MQTT client fails silently or raises exceptions

**Why it happens:**
- Network interruptions
- Broker restarts
- Client reconnection not complete
- Race between connection and publish

**How to avoid:**
1. Always check `client.is_connected()` before publishing
2. Use QoS > 0 for important messages
3. Handle publish failures:
```python
result = client.publish(topic, payload, qos=1, retain=True)
if result.rc != mqtt.MQTT_ERR_SUCCESS:
    logging.warning(f"Failed to publish: {mqtt.error_string(result.rc)}")
```
4. Use `loop_forever()` which handles reconnection automatically
5. For `loop_start()`, implement `on_connect` to track state

**Warning signs:**
- "client is not currently connected" errors
- Messages not reaching broker
- Service appears running but ineffective

**Sources:**
- [MQTT Client Auto-Reconnect Best Practices](https://www.emqx.com/en/blog/mqtt-client-auto-reconnect-best-practices)
- [Paho Python MQTT Client Connections](http://www.steves-internet-guide.com/client-connections-python-mqtt/)

### Pitfall 3: Systemd Restart Loop Protection

**What goes wrong:** Service fails repeatedly, hits StartLimit, systemd stops restarting it permanently

**Why it happens:**
- Default `StartLimitIntervalSec=10s` and `StartLimitBurst=5`
- Service enters failed state after 5 restarts in 10 seconds
- No automatic recovery without manual intervention

**How to avoid:**
1. Set appropriate limits for long-running services:
```ini
[Service]
Restart=on-failure
RestartSec=5s
StartLimitIntervalSec=300
StartLimitBurst=10
```

2. Use exponential backoff:
```ini
RestartSteps=5
RestartMaxDelaySec=300
```

3. For critical services, consider indefinite restarts:
```ini
StartLimitIntervalSec=0  # Disable limit
```

4. Reset failed state after fixing issues:
```bash
systemctl --user reset-failed <service>
```

**Warning signs:**
- Service shows "inactive (failed)"
- Service won't start even after fixing bug
- Logs show "Start request repeated too quickly"

**Sources:**
- [Systemd Service Retry Configuration](https://ithy.com/article/systemd-service-retry-on-failure-config-z9026h7u)
- [Systemd Indefinite Service Restarts](https://michael.stapelberg.ch/posts/2024-01-17-systemd-indefinite-service-restarts/)
- [Auto-recovery with Systemd](https://singlebrook.com/2017/10/23/auto-restart-crashed-service-systemd/)

### Pitfall 4: Status File Race Conditions

**What goes wrong:** Reader gets partial/corrupted data, empty files, or misses updates

**Why it happens:**
- Writer doesn't write atomically
- Reader reads during write
- Multiple writers to same file
- No locking mechanism

**How to avoid:**
1. Atomic writes using temp file + rename:
```python
import os
from pathlib import Path

def atomic_write(file_path, content):
    tmp_path = file_path.with_suffix('.tmp')
    tmp_path.write_text(content)
    os.rename(tmp_path, file_path)  # Atomic on POSIX
```

2. Validate content before acting:
```python
content = file_path.read_text().strip()
if content not in VALID_STATES:
    logging.warning(f"Invalid state: {content}")
    return DEFAULT_STATE
```

3. Use watchdog for change detection, not polling
4. Handle FileNotFoundError gracefully (file may not exist yet)

**Warning signs:**
- Intermittent unexpected behavior
- Empty string states
- Services see invalid states
- Logs show "invalid state" warnings

### Pitfall 5: Circular Dependencies in Idle Detection

**What goes wrong:** System locks when it shouldn't, or never locks when it should

**Why it happens:**
- Local idle detection depends on HA feedback
- HA feedback depends on local status reports
- Network/MQTT issues break the loop
- Logic becomes unpredictable

**How to avoid:**
1. Design fallback behavior for every external dependency:
```python
# If HA says "in_office=off", lock immediately
# If HA unavailable, use time-based fallback (30min timeout)
if in_office_status is None:
    # HA unavailable - use fallback
    use_time_based_locking = True
```

2. Separate concerns:
   - Idle detection (local, always works)
   - Presence detection (HA-dependent, fallback needed)
   - Action execution (combines both)

3. Make HA integration optional:
```python
if mqtt_available and ha_presence_known:
    # Use smart presence-based locking
else:
    # Use simple time-based locking
```

**Warning signs:**
- System locks user out when they're present
- System never locks even when away
- Behavior changes with network status
- "Waiting for MQTT" messages in logs

## Code Examples

### Example 1: Robust MQTT Connection with Reconnection

```python
import paho.mqtt.client as mqtt
import time
import logging

# Configuration
BROKER = "10.20.10.100"
PORT = 1883
CLIENT_ID = "linux_mini_mqtt_reports"
KEEPALIVE = 60

# State tracking
broker_online = False

def on_connect(client, userdata, flags, rc):
    global broker_online
    if rc == 0:
        logging.info("Connected to MQTT broker")
        broker_online = True

        # Always resubscribe on connect (important for reconnection)
        client.subscribe("your/topic", qos=1)

        # Publish online status
        client.publish(
            f"devices/{CLIENT_ID}/status",
            payload="online",
            qos=1,
            retain=True
        )
    else:
        logging.error(f"Connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    global broker_online
    broker_online = False
    logging.warning(f"Disconnected with reason code {rc}")
    # Don't call reconnect here - loop_forever() handles it

def on_message(client, userdata, message):
    logging.debug(f"Received: {message.topic} = {message.payload.decode()}")
    # Process message

# Create client
client = mqtt.Client(client_id=CLIENT_ID)
client.username_pw_set(username=USERNAME, password=PASSWORD)

# Set callbacks
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Set will message for clean offline detection
client.will_set(
    f"devices/{CLIENT_ID}/status",
    payload="offline",
    qos=1,
    retain=True
)

# Configure automatic reconnection
client.reconnect_delay_set(min_delay=1, max_delay=120)

# Connect and start loop (handles reconnection automatically)
try:
    client.connect(BROKER, PORT, KEEPALIVE)
    client.loop_forever()  # Blocks, auto-reconnects on disconnect
except KeyboardInterrupt:
    logging.info("Shutting down")
    client.disconnect()
```

**Source:** Based on [Paho-MQTT documentation](https://pypi.org/project/paho-mqtt/) and best practices from [EMQX MQTT guide](https://www.emqx.com/en/blog/how-to-use-mqtt-in-python)

### Example 2: Atomic Status File Updates with Watchdog

```python
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import os

class StatusFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_modified(self, event):
        if event.src_path.endswith('/status_file'):
            self.callback(event.src_path)

def atomic_write_status(file_path: Path, content: str):
    """Write status file atomically using temp file + rename."""
    tmp_path = file_path.with_suffix('.tmp')
    try:
        tmp_path.write_text(content)
        os.rename(tmp_path, file_path)  # Atomic on POSIX
        logging.debug(f"Wrote {content} to {file_path}")
    except Exception as e:
        logging.error(f"Failed to write status: {e}")
        tmp_path.unlink(missing_ok=True)

def read_status_safe(file_path: Path, valid_states: set, default: str):
    """Read status file with validation."""
    try:
        content = file_path.read_text().strip()
        if content in valid_states:
            return content
        else:
            logging.warning(f"Invalid state '{content}', using default '{default}'")
            return default
    except FileNotFoundError:
        logging.debug(f"Status file not found, using default '{default}'")
        return default
    except Exception as e:
        logging.error(f"Error reading status: {e}")
        return default

# Usage
status_file = Path("/tmp/mqtt/linux_mini_status")
valid_states = {"active", "inactive"}

# Write
atomic_write_status(status_file, "active")

# Read
current_state = read_status_safe(status_file, valid_states, default="active")

# Watch for changes
def on_status_change(file_path):
    state = read_status_safe(Path(file_path), valid_states, "active")
    logging.info(f"Status changed to: {state}")

observer = Observer()
observer.schedule(
    StatusFileHandler(on_status_change),
    path=str(status_file.parent),
    recursive=False
)
observer.start()
```

### Example 3: Systemd Service with Proper Restart Policy

```ini
[Unit]
Description=MQTT Reports Service
After=network.target
# Ensure network is actually up before starting
Wants=network-online.target
After=network-online.target

[Service]
Type=simple

# Runtime directory for temporary files
RuntimeDirectory=mqtt
RuntimeDirectoryMode=755

# Environment
Environment=PYTHONPATH=/home/rash/.config/scripts
WorkingDirectory=/home/rash/.config/scripts/mqtt

# Load secrets from .env file
ExecStartPre=/usr/bin/bash -c "source /home/rash/.config/scripts/mqtt/.env && echo 'Environment loaded'"

# Main command
ExecStart=/home/rash/.config/scripts/mqtt/launch_mqtt_services.sh mqtt_reports

# Restart configuration
Restart=on-failure
RestartSec=5s

# Prevent excessive restarts (allow 10 restarts in 5 minutes)
StartLimitIntervalSec=300
StartLimitBurst=10

# Exponential backoff for restarts
RestartSteps=5
RestartMaxDelaySec=120

# Logging
StandardOutput=journal
StandardError=journal

# Resource limits (optional but recommended)
MemoryMax=100M
CPUQuota=50%

[Install]
WantedBy=default.target
```

### Example 4: Health Check Script

```python
#!/usr/bin/env python3
"""
Health check for idle detection system.
Returns 0 if healthy, 1 if issues detected.
"""
import sys
from pathlib import Path
import subprocess

def check_service(service_name):
    """Check if systemd service is running."""
    result = subprocess.run(
        ["systemctl", "--user", "is-active", service_name],
        capture_output=True,
        text=True
    )
    return result.stdout.strip() == "active"

def check_status_file(file_path, valid_states):
    """Check if status file exists and has valid content."""
    try:
        content = Path(file_path).read_text().strip()
        return content in valid_states
    except:
        return False

def main():
    issues = []

    # Check critical services
    services = [
        "hypridle.service",
        "mqtt_reports.service",
        "mqtt_listener.service",
        "in-office-monitor.service"
    ]

    for service in services:
        if not check_service(service):
            issues.append(f"Service {service} is not running")

    # Check status files
    status_files = {
        "/tmp/mqtt/linux_mini_status": {"active", "inactive"},
        "/tmp/mqtt/idle_detection_status": {"inactive", "in_progress"},
        "/tmp/mqtt/in_office_status": {"on", "off"}
    }

    for file_path, valid_states in status_files.items():
        if not check_status_file(file_path, valid_states):
            issues.append(f"Status file {file_path} is missing or invalid")

    # Check MQTT connectivity
    mqtt_status = Path("/tmp/mqtt/in_office_status")
    if not mqtt_status.exists():
        issues.append("MQTT listener not receiving messages (in_office_status missing)")

    # Report results
    if issues:
        print("❌ Health check FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    else:
        print("✅ All checks passed")
        return 0

if __name__ == "__main__":
    sys.exit(main())
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Polling files in loops | inotify-based watchdog | Current system | Efficient, event-driven |
| Custom config in each script | Centralized config.py | Current system | Single source of truth |
| Simple time-based locking | HA presence integration | Current system | Smarter, context-aware |
| No status visibility | Waybar integration | Current system | User can see system state |

**Deprecated/outdated:**
- Face detection: config.py references `face_presence` status file but no script implements it
- Motion detection: config.py has motion detection parameters but not actively used
- Manual override: UI exists but unclear if it's actually working

**Modern best practices:**
- Use hypridle's native `ignore_dbus_inhibit` instead of custom inhibit detection
- Let systemd handle service supervision instead of custom watchdog scripts
- Use MQTT retained messages for status persistence instead of relying on file system

## Open Questions

1. **Face detection status**
   - What we know: Code references face_presence detection methods
   - What's unclear: Is this feature active? Scripts missing?
   - Recommendation: Remove unused code or document if it's work-in-progress

2. **Manual override functionality**
   - What we know: UI elements exist, status file defined
   - What's unclear: How does user trigger it? Is it working?
   - Recommendation: Test the feature, document usage

3. **Webcam status monitoring**
   - What we know: `linux_webcam_status.py` exists, MQTT sensor defined
   - What's unclear: Is this actively preventing screen lock during video calls?
   - Recommendation: Test with active webcam usage

4. **Home Assistant automation reliability**
   - What we know: HA publishes to `rob_in_office` topic
   - What's unclear: What triggers HA to update this? Is it reliable?
   - Recommendation: Review HA automations in `/home/rash/ext_repos/ha-config/automations.yaml`

5. **Fallback behavior**
   - What we know: Time-based fallback exists (30min timeout)
   - What's unclear: Does it activate when MQTT is down? Has it been tested?
   - Recommendation: Test with MQTT broker offline

## Sources

### Primary (HIGH confidence)
- Hypridle official documentation - https://wiki.hypr.land/Hypr-Ecosystem/hypridle/
- Paho-MQTT PyPI page - https://pypi.org/project/paho-mqtt/
- Paho-MQTT migration guide - https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html
- Systemd service documentation - https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html
- Local codebase analysis (direct file inspection)

### Secondary (MEDIUM confidence)
- Paho-MQTT version 2 guide - http://www.steves-internet-guide.com/paho-mqtt-python-client-version-2/
- MQTT auto-reconnect best practices - https://www.emqx.com/en/blog/mqtt-client-auto-reconnect-best-practices
- Systemd indefinite restarts - https://michael.stapelberg.ch/posts/2024-01-17-systemd-indefinite-service-restarts/
- Systemd service retry config - https://ithy.com/article/systemd-service-retry-on-failure-config-z9026h7u

### Tertiary (LOW confidence)
- General MQTT Python patterns from search results
- Community systemd best practices

## Metadata

**Confidence breakdown:**
- Critical bug identification: HIGH - Directly observed in logs and code
- MQTT reconnection issues: HIGH - Logs show repeated failures
- Systemd restart policies: MEDIUM - Current config is minimal, best practices from docs
- Architecture understanding: HIGH - Comprehensive code review completed
- Fix strategies: HIGH - Based on official documentation and observed bugs

**Research date:** 2026-02-12
**Valid until:** 2026-03-12 (30 days - stable technologies)

**Key constraints for planner:**
- Must maintain paho-mqtt 1.6.x compatibility OR migrate all code to 2.0 API
- Cannot modify Home Assistant configuration (separate repo)
- Must not break existing Waybar integration
- System must continue working with MQTT/HA offline (fallback mode)
- All changes must be deployed via setup.py (dotfiles workflow)
