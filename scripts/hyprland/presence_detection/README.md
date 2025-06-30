# Simplified Idle Detection System

A streamlined idle management system that provides basic timeout-based locking and display management for Hyprland, with office presence integration.

## System Overview

This system provides simple, reliable idle detection with three stages:

1. **30 seconds**: Report inactive status to Home Assistant
2. **60 seconds**: Check office presence, lock if away from office
3. **90 seconds**: Check office presence again, turn off displays if still away
4. **Background**: Continuous monitoring to turn displays back on when returning to office

## Current Status

**✅ ACTIVE COMPONENTS:**
- Simple timeout-based idle detection
- Office presence integration
- MQTT status reporting
- Basic locking and display management

**🚫 DISABLED COMPONENTS (preserved for future use):**
- Face detection system (`continuous_face_monitor.py`, `face_detector.py`)
- Advanced idle management (`office_status_handler.py`)
- Complex parallel processing

## Architecture

```
hypridle.conf (Simplified)
    ├── 30s: activity_status_reporter.py --inactive
    ├── 60s: idle_simple_lock.py
    ├── 90s: idle_simple_dpms.py
    └── on-resume: idle_simple_resume.py

launch.conf
    └── startup: in_office_monitor.py (continuous background)
```

## File Structure

```
scripts/
├── ha/
│   ├── init_presence_status.py      # Boot-time status initialization
│   └── activity_status_reporter.py  # Activity status reporting
├── hyprland/
│   ├── idle_simple_lock.py          # 60s: Lock if office status off
│   ├── idle_simple_dpms.py          # 90s: DPMS off if office status still off
│   ├── idle_simple_resume.py        # Resume: Report active, DPMS on
│   └── in_office_monitor.py         # Background: DPMS on when office status → on
└── hyprland/presence_detection/     # DISABLED COMPONENTS (preserved)
    ├── face_detector.py             # [DISABLED] Face detection engine
    ├── continuous_face_monitor.py   # [DISABLED] Face monitoring
    ├── office_status_handler.py     # [DISABLED] Advanced office handler
    └── cleanup_on_resume.py         # [DISABLED] Complex cleanup
```

## Script Responsibilities

### Active Scripts

#### `init_presence_status.py`
- **Purpose**: Initialize status files on boot and clean up stale flags
- **Called**: Once at Hyprland launch via `launch.conf`
- **Actions**:
  - Cleans up stale exit flags from previous sessions
  - Creates required `/tmp/mqtt/` status files with defaults
- **Status Files Created**:
  - `linux_mini_status`: `"active"`
  - `idle_detection_status`: `"inactive"`
  - `in_office_status`: `"on"`

#### `activity_status_reporter.py`
- **Purpose**: Report user activity status to Home Assistant
- **Called**: By hypridle at 30s timeout and on resume
- **Arguments**: `--active` or `--inactive`
- **Updates**:
  - `/tmp/mqtt/linux_mini_status`
  - `/tmp/mqtt/idle_detection_status`

#### `idle_simple_lock.py`
- **Purpose**: Check office status and lock if away from office, with continuous monitoring
- **Called**: By hypridle at 60s timeout
- **Behavior**:
  - Reads `/tmp/mqtt/in_office_status`
  - If status is "off": Lock screen immediately with hyprlock
  - If status is "on": Continuously monitor for status change to "off", then lock
  - If user resumes activity during monitoring: Stop monitoring via exit flag mechanism
- **Enhanced Logic**:
  - **Critical Fix**: No longer skips locking when in_office=on at timeout
  - Instead monitors continuously until either office status changes to "off" (triggers lock) or user activity resumes (stops monitoring)
  - Uses `/tmp/idle_simple_lock_exit` flag for clean shutdown when user resumes

#### `idle_simple_dpms.py`
- **Purpose**: Check office status and turn off displays if still away
- **Called**: By hypridle at 90s timeout
- **Behavior**:
  - Reads `/tmp/mqtt/in_office_status`
  - If status is "off": Turn off displays (DPMS off)
  - If status is "on": Do nothing (skip DPMS off)

#### `idle_simple_resume.py`
- **Purpose**: Handle user resume/activity detection and signal lock monitoring to stop
- **Called**: By hypridle on resume (any user activity)
- **Actions**:
  1. Create exit flag (`/tmp/idle_simple_lock_exit`) to stop any running lock monitoring
  2. Ensure displays are turned on (DPMS on)
  3. Report active status to Home Assistant
  4. Clean up exit flag after a brief delay

#### `in_office_monitor.py`
- **Purpose**: Continuously monitor office status changes
- **Called**: At startup via `launch.conf` (runs continuously)
- **Behavior**:
  - Monitors `/tmp/mqtt/in_office_status` for changes
  - When status changes from "off" → "on": Immediately turn on displays
  - Runs in background, responds instantly to office status changes

### Disabled Scripts (Preserved)

#### `face_detector.py` [DISABLED]
- **Status**: Face detection temporarily disabled
- **Purpose**: Computer vision face detection (preserved for future use)
- **Behavior**: Early return with disabled message if accidentally called

#### `continuous_face_monitor.py` [DISABLED]
- **Status**: Face monitoring temporarily disabled
- **Purpose**: Face detection coordination (preserved for future use)
- **Behavior**: Early return with disabled message if accidentally called

#### `office_status_handler.py` [DISABLED]
- **Status**: Advanced office handling temporarily disabled
- **Purpose**: Complex office-based management (preserved for future use)
- **Behavior**: Early return with disabled message if accidentally called

## Status Files

All status files are located in `/tmp/mqtt/` and monitored by `mqtt_reports.py`:

### Active Status Files

| File | Values | Purpose | Updated By |
|------|--------|---------|------------|
| `linux_mini_status` | `active`, `inactive` | User activity state | `activity_status_reporter.py`, `toggle_hypridle.py` |
| `idle_detection_status` | `inactive`, `in_progress` | Idle detection state | `activity_status_reporter.py`, `toggle_hypridle.py` |
| `in_office_status` | `on`, `off` | Office occupancy | External MQTT |
| `manual_override_status` | `active`, `inactive` | Manual override state | `toggle_hypridle.py` |

### Disabled Status Files (Not Used)

| File | Status | Purpose |
|------|--------|---------|
| `face_presence` | **DISABLED** | Face detection results (not created/used) |

### Control Files

| File | Purpose | Created By |
|------|---------|------------|
| `/tmp/in_office_monitor_exit` | Stop in-office monitor | Cleanup scripts |
| `/tmp/idle_simple_lock_exit` | Stop lock monitoring when user resumes | `idle_simple_resume.py` |

## System Flow

### Boot Sequence
1. **Hyprland starts** → `launch.conf` executes
2. **`init_presence_status.py`** → Creates status files with defaults
3. **`in_office_monitor.py`** → Starts continuous background monitoring
4. **System ready** → Simple idle detection active

### Simplified Idle Detection Flow

```
User becomes idle (30s)
    ↓
activity_status_reporter.py --inactive
    ↓ (writes status files)
    ├── linux_mini_status = "inactive"
    └── idle_detection_status = "in_progress"

User idle continues (60s)
    ↓
idle_simple_lock.py
    ↓
Check in_office_status
    ├── "off" → Lock screen immediately (hyprlock)
    └── "on"  → Monitor continuously for status change to "off"
                ├── Status changes to "off" → Lock screen
                └── User resumes activity → Stop monitoring (exit flag)

User idle continues (90s)
    ↓
idle_simple_dpms.py
    ↓
Check in_office_status
    ├── "off" → Turn off displays (DPMS off)
    └── "on"  → Do nothing

Meanwhile (CONTINUOUS)
    ↓
in_office_monitor.py (background)
    ↓
Monitor in_office_status changes
    └── "off" → "on" → IMMEDIATELY turn on displays

User resumes activity (ANY TIME)
    ↓
idle_simple_resume.py
    ↓
1. DPMS on → Ensure displays active
2. Report active status → Update Home Assistant
```

### Decision Logic

#### Lock Decision (60s) - Enhanced
```
idle_simple_lock.py
    ↓
Read /tmp/mqtt/in_office_status
    ├── "off" → Lock screen immediately (away from office)
    └── "on"  → Start continuous monitoring
                    ↓
                Monitor for status change or user activity
                    ├── in_office changes to "off" → Lock screen
                    └── User activity detected (exit flag) → Stop monitoring
```

#### DPMS Decision (90s)
```
idle_simple_dpms.py
    ↓
Read /tmp/mqtt/in_office_status
    ├── "off" → DPMS off (still away, turn off displays)
    └── "on"  → Skip (in office, keep displays on)
```

#### Continuous Monitoring
```
in_office_monitor.py (always running)
    ↓
Watch /tmp/mqtt/in_office_status for changes
    ↓
Status changed from "off" to "on"?
    └── YES → DPMS on immediately (returned to office)
```

## Configuration

### Hypridle Configuration (`hypridle.conf`)
```conf
# Stage 1: 30 seconds - report inactive status
listener {
    timeout = 30
    on-timeout = ~/.config/scripts/ha/activity_status_reporter.py --inactive
    on-resume = ~/.config/scripts/hyprland/idle_simple_resume.py
}

# Stage 2: 60 seconds - check in_office and lock if off
listener {
    timeout = 60
    on-timeout = ~/.config/scripts/hyprland/idle_simple_lock.py
}

# Stage 3: 90 seconds - check in_office again and dpms off if still off
listener {
    timeout = 90
    on-timeout = ~/.config/scripts/hyprland/idle_simple_dpms.py
}
```

### Launch Configuration (`launch.conf`)
```conf
# Initialize presence detection status files
exec-once = ~/.config/scripts/ha/init_presence_status.py

# Start in-office monitor continuously
exec-once = ~/.config/scripts/hyprland/in_office_monitor.py &
```

## Integration Points

### MQTT Integration
- **Publisher**: `mqtt_reports.py` monitors `/tmp/mqtt/` files
- **Consumer**: Home Assistant receives status updates
- **External Input**: Office status received via MQTT from motion sensors

### Waybar Integration
- **Display**: Status files drive waybar indicators
- **Manual Override**: Click hypridle module to manually disable/enable idle detection
- **Files Used**: Various `/tmp/mqtt/` status files for UI updates
- **Toggle Script**: `toggle_hypridle.py` manages manual override with full MQTT integration

### Hyprland Integration
- **Idle Detection**: hypridle triggers scripts at defined timeouts
- **Display Control**: `hyprctl dispatch dpms on/off`
- **Locking**: `hyprlock` for screen locking

## Debugging

### Log Files
- **In-office Monitor**: `/tmp/in_office_monitor.log`
- **Simple Lock**: `/tmp/idle_simple_lock.log`
- **Simple DPMS**: `/tmp/idle_simple_dpms.log`
- **Simple Resume**: `/tmp/idle_simple_resume.log`
- **Activity Reporter**: `/tmp/mini_status_debug.log`
- **Manual Override**: `/tmp/hypridle_toggle.log`

### Manual Testing
```bash
# Check current status
cat /tmp/mqtt/linux_mini_status
cat /tmp/mqtt/idle_detection_status
cat /tmp/mqtt/in_office_status

# Test activity reporting
~/.config/scripts/ha/activity_status_reporter.py --active
~/.config/scripts/ha/activity_status_reporter.py --inactive

# Test locking behavior
~/.config/scripts/hyprland/idle_simple_lock.py

# Test DPMS behavior
~/.config/scripts/hyprland/idle_simple_dpms.py

# Test resume behavior
~/.config/scripts/hyprland/idle_simple_resume.py

# Test office status changes
echo "off" > /tmp/mqtt/in_office_status
echo "on" > /tmp/mqtt/in_office_status

# Test manual override
~/.config/scripts/waybar/toggle_hypridle.py  # Toggle once to disable
~/.config/scripts/waybar/toggle_hypridle.py  # Toggle again to re-enable
```

**Lock monitoring:**
```bash
# Test enhanced lock behavior
~/.config/scripts/hyprland/idle_simple_lock.py  # Will lock immediately if in_office=off, or start monitoring if in_office=on

# Test exit flag mechanism
touch /tmp/idle_simple_lock_exit  # Should stop any running lock monitoring

# Monitor lock behavior in real-time
tail -f /tmp/idle_simple_lock.log

# Test office status change during monitoring
echo "on" > /tmp/mqtt/in_office_status    # Start lock monitoring (if idle_simple_lock.py running)
echo "off" > /tmp/mqtt/in_office_status   # Should trigger lock during monitoring
```

### Process Monitoring
```bash
# Check running processes
ps aux | grep -E "(in_office_monitor)"

# Check for exit flags
ls -la /tmp/*_exit 2>/dev/null || echo "No exit flags present"

# Monitor status file changes
watch -n1 'cat /tmp/mqtt/*_status 2>/dev/null'

# Monitor in-office changes live
tail -f /tmp/in_office_monitor.log

# Monitor manual override actions
tail -f /tmp/hypridle_toggle.log
```

## Manual Override System

### Waybar Module Integration
The hypridle status is displayed in waybar and can be manually controlled:

**Waybar Module Configuration:**
```json
"custom/hypridle": {
    "format": "{}",
    "exec": "jq -r '.text // \"⚫\"' /tmp/waybar/idle_status.json 2>/dev/null || echo '⚫'",
    "interval": 1,
    "on-click": "~/.config/scripts/waybar/toggle_hypridle.py",
    "tooltip": false
}
```

**Manual Override Behavior:**
- **Click once**: Disable hypridle (manual override ON)
- **Click again**: Re-enable hypridle (manual override OFF)
- **Status indicators**: ⚫ = running, 🔴 = disabled

### MQTT Integration for Manual Override

When manually toggling hypridle via waybar:

**Disabling Hypridle (Override ON):**
```bash
manual_override_status = "active"
linux_mini_status = "active"         # User is present
idle_detection_status = "inactive"   # Idle detection stopped
```

**Re-enabling Hypridle (Override OFF):**
```bash
manual_override_status = "inactive"
linux_mini_status = "active"         # User is active
idle_detection_status = "inactive"   # Ready but not running
```

**Additional Actions:**
- Calls `activity_status_reporter.py --active` for consistency
- Logs all toggle actions with timestamps to `/tmp/hypridle_toggle.log`
- Updates waybar status immediately

### Manual Override Script: `toggle_hypridle.py`
- **Purpose**: Handle manual hypridle enable/disable with full MQTT integration
- **Called**: By waybar module click, or manually
- **Features**:
  - Kills/starts hypridle process
  - Updates all relevant MQTT status files
  - Maintains consistency with activity reporting
  - Logs all actions for debugging
  - Provides immediate waybar feedback

## Key Features

### Simplicity
- Clear 3-stage timeout progression
- No complex parallel processing
- Predictable behavior and timing

### Manual Control
- One-click disable/enable via waybar
- Full MQTT integration for manual overrides
- Consistent status reporting across all systems
- Logged actions for debugging and tracking

### Enhanced Reliability
- **Critical Bug Fix**: Lock monitoring no longer skips when in_office=on at 60s timeout
- **Continuous Monitoring**: Locks screen as soon as office status changes to "off"
- **Clean Exit Handling**: Proper shutdown of lock monitoring when user activity resumes
- **No Missed Locks**: System will always attempt to lock when user leaves office, regardless of timing

### Responsive
- Immediate display activation when returning to office
- Fast resume response (< 1 second)
- No polling delays for critical state changes
- Instant manual override response

### Office Integration
- Respects office presence for all decisions
- Smart locking (only when away from office)
- Smart display management (context-aware)

## Disabled Components

The following components are **disabled but preserved** for potential future reactivation:

### Face Detection System
- **Files**: `face_detector.py`, `continuous_face_monitor.py`
- **Status**: Commented out, early returns added
- **Reason**: Simplifying system, removing camera dependency

### Advanced Office Handler
- **Files**: `office_status_handler.py`
- **Status**: Disabled via early return
- **Reason**: Replaced with simpler timeout-based approach

### Complex Cleanup
- **Files**: `cleanup_on_resume.py`
- **Status**: Updated to handle simplified system only
- **Reason**: Less complex state to manage

## Troubleshooting

### Common Issues

**Locking not working:**
- Check `/tmp/mqtt/in_office_status` file exists and has correct value
- Verify hyprlock is installed and working
- Check `idle_simple_lock.log` for errors
- **New**: Check if lock monitoring is running correctly when in_office=on
- **New**: Verify exit flag mechanism works when user resumes activity

**Displays not turning off:**
- Verify in_office_status is "off" when expected
- Check `idle_simple_dpms.log` for hyprctl errors
- Test manual DPMS: `hyprctl dispatch dpms off`

**Displays not turning back on:**
- Check `in_office_monitor.py` is running: `ps aux | grep in_office_monitor`
- Verify office status changes are detected in logs
- Test manual DPMS: `hyprctl dispatch dpms on`

**Office status not updating:**
- Verify MQTT connection and `mqtt_reports.py` service
- Check file permissions on `/tmp/mqtt/in_office_status`
- Ensure motion sensors are reporting to Home Assistant

**Manual override not working:**
- Check waybar configuration includes the `on-click` action
- Verify `toggle_hypridle.py` is executable
- Check `/tmp/hypridle_toggle.log` for toggle action logs
- Ensure MQTT status files are writable

**Scripts not starting:**
- Check hypridle configuration syntax
- Verify script permissions (executable)
- Check individual script logs for errors

**Waybar not updating:**
- Check waybar service is running: `systemctl --user status waybar`
- Verify status file paths in waybar configuration
- Test manual status file updates

**Lock monitoring issues:**
- Check `/tmp/idle_simple_lock.log` for monitoring status and exit flag handling
- Verify `/tmp/idle_simple_lock_exit` flag is created/cleaned up properly by resume script
- Test manual exit flag: `touch /tmp/idle_simple_lock_exit` (should stop monitoring)
- Monitor continuous lock behavior: `tail -f /tmp/idle_simple_lock.log`

## Migration Notes

This system was simplified from a more complex parallel processing system that included:
- Computer vision face detection
- Complex state management
- Multiple parallel monitoring processes

The disabled components remain in the codebase for potential future reactivation if needed.
