# Optimized Idle Management System with Advanced Face Detection

A streamlined idle management system that provides reliable timeout-based locking and display management for Hyprland, with advanced MediaPipe-based face detection and office presence detection.

## System Overview

This system provides intelligent idle detection with four stages:

1. **Stage 1**: Report inactive status and start presence checking phase
2. **Stage 2**: Perform face detection to verify user presence
3. **Stage 3**: Check office presence, lock if away from office (respects face detection)
4. **Stage 4**: Check office presence, turn off displays if away from office (continuous monitoring)
5. **Background**: Continuous monitoring to turn displays back on when returning to office

## Architecture

```
hypridle.conf
    ├── Stage 1: activity_status_reporter.py --inactive (starts presence checking)
    ├── Stage 2: face_detector.py (face presence verification)
    ├── Stage 3: idle_simple_lock.py (respects face detection results)
    ├── Stage 4: idle_simple_dpms.py
    └── on-resume: idle_simple_resume.py

launch.conf
    └── startup: in_office_monitor.py (continuous background)
```

## File Structure

```
scripts/
├── mqtt/
│   ├── mqtt_reports.py                # Status reporting to MQTT (kept separate)
│   └── mqtt_listener.py               # MQTT message handling (kept separate)
└── hyprland/
    └── idle_management/
        ├── config.py                      # 🆕 Centralized configuration for all scripts
        ├── init_presence_status.py        # Boot-time status initialization
        ├── activity_status_reporter.py    # Activity status + presence checking
        ├── linux_webcam_status.py         # Webcam monitoring (filtered)
        ├── idle_simple_lock.py            # Stage 3: Lock if office status off
        ├── idle_simple_dpms.py            # Stage 4: DPMS off if office status off (continuous monitoring)
        ├── idle_simple_resume.py          # Resume: Report active, DPMS on
        ├── in_office_monitor.py           # Background: DPMS on when office status → on
        ├── face_detector.py               # Advanced human presence detection engine
        └── debug/
            └── debug_idle_temp_files.py   # Comprehensive system state monitor
```

## Script Responsibilities

#### `init_presence_status.py`
- **Purpose**: Initialize status files on boot and clean up stale flags
- **Called**: Once at Hyprland launch via `launch.conf`
- **Actions**:
  - Cleans up stale exit flags from previous sessions
  - Creates required `/tmp/mqtt/` status files with defaults
- **Status Files Created**:
  - `linux_mini_status`: `"active"`
  - `idle_detection_status`: `"inactive"`
  - `face_presence`: `"not_detected"`
  - `linux_webcam_status`: `"inactive"`
  - `in_office_status`: `"on"`

#### `activity_status_reporter.py`
- **Purpose**: Report user activity status and start presence checking phase
- **Called**: By hypridle at Stage 1 timeout and on resume
- **Arguments**: `--active` or `--inactive`
- **Behavior**:
  - `--inactive`: Sets `idle_detection_status` to "in_progress" (starts presence checking phase)
  - `--active`: Sets `idle_detection_status` to "inactive" (stops presence checking)
- **Updates**:
  - `/tmp/mqtt/linux_mini_status`
  - `/tmp/mqtt/idle_detection_status`

#### `face_detector.py`
- **Purpose**: Advanced human presence detection using cutting-edge computer vision
- **Called**: By hypridle at Stage 2 timeout
- **Detection Methods** (Optimized for reliability and edge cases):
  - **MediaPipe Face Mesh**: State-of-the-art face detection for all angles, orientations, and lighting conditions ✨
    - Handles looking down at phone, tilted heads, partial occlusion
    - Uses 468 facial landmarks for precise detection
    - Excellent performance in edge cases where traditional methods fail
  - **Motion Detection**: Detects subtle movements and user interactions ✨
- **Detection Logic**:
  - Starts with 1-second detection window
  - Uses optimized detection methods simultaneously
  - 50% threshold for human presence (≥50% = detected)
  - If not detected in 1s, extends window by 1s up to 10s total
  - Continuous monitoring every 60s if human presence detected
- **Status Reporting**:
  - Reports `"in_progress"` to `idle_detection_status` at start
  - Reports `"detected"` or `"not_detected"` to `face_presence`
  - Logs breakdown of which detection methods were used
  - Resets both statuses if user becomes active
- **Smart Exit**: Monitors `linux_mini_status` for user activity
- **Logging**: Comprehensive logging to `/tmp/face_detector.log` with detection method breakdown

#### `linux_webcam_status.py`
- **Purpose**: Monitor webcam usage by non-automated processes
- **Enhanced Filtering**: Excludes face detector processes from webcam "active" status
- **Behavior**:
  - Uses `lsof` to detect camera usage
  - Filters out `face_detector.py` processes
  - Only reports "active" for genuine user webcam usage
- **Integration**: Prevents false positives during automated face detection

#### `idle_simple_lock.py`
- **Purpose**: Check office status and lock if away from office, with continuous monitoring
- **Called**: By hypridle at Stage 3 timeout
- **Behavior**:
  - Reads `/tmp/mqtt/in_office_status` (influenced by face detection via HA automation)
  - If status is "off": Lock screen immediately with hyprlock
  - If status is "on": Continuously monitor for status change to "off", then lock
  - If user resumes activity during monitoring: Stop monitoring via exit flag mechanism
- **Integration**: Respects face detection results via Home Assistant automation

#### `idle_simple_dpms.py`
- **Purpose**: Check office status and turn off displays if away from office, with continuous monitoring
- **Called**: By hypridle at Stage 4 timeout
- **Behavior**:
  - Reads `/tmp/mqtt/in_office_status` (influenced by face detection via HA automation)
  - If status is "off": Turn off displays immediately (DPMS off)
  - If status is "on": Continuously monitor for status change to "off", then turn off displays
  - If user resumes activity during monitoring: Stop monitoring via exit flag mechanism
- **Integration**: Respects face detection results via Home Assistant automation

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

## Status Files

All status files are located in `/tmp/mqtt/` and monitored by `mqtt_reports.py`:

| File | Values | Purpose | Updated By |
|------|--------|---------|------------|
| `linux_mini_status` | `active`, `inactive` | User activity state | `activity_status_reporter.py`, `toggle_hypridle.py` |
| `idle_detection_status` | `inactive`, `in_progress` | Idle detection state | `activity_status_reporter.py`, `face_detector.py`, `toggle_hypridle.py` |
| `face_presence` | `detected`, `not_detected` | Face detection results | `face_detector.py` |
| `linux_webcam_status` | `active`, `inactive` | Non-automated webcam usage | `linux_webcam_status.py` |
| `in_office_status` | `on`, `off` | Office occupancy | External MQTT (influenced by face detection) |
| `manual_override_status` | `active`, `inactive` | Manual override state | `toggle_hypridle.py` |

### Control Files

| File | Purpose | Created By |
|------|---------|------------|
| `/tmp/in_office_monitor_exit` | Stop in-office monitor | Cleanup scripts |
| `/tmp/idle_simple_lock_exit` | Stop lock and DPMS monitoring when user resumes | `idle_simple_resume.py` |

## System Flow

### Boot Sequence
1. **Hyprland starts** → `launch.conf` executes
2. **`init_presence_status.py`** → Creates status files with defaults
3. **`in_office_monitor.py`** → Starts continuous background monitoring
4. **System ready** → Advanced idle detection with face recognition active

### Advanced Idle Detection Flow

```
User becomes idle (Stage 1)
    ↓
activity_status_reporter.py --inactive
    ↓ (writes status files)
    ├── linux_mini_status = "inactive"
    └── idle_detection_status = "in_progress" (starts presence checking phase)

User idle continues (Stage 2)
    ↓
face_detector.py
    ↓ (maintains status)
    ├── idle_detection_status = "in_progress" (continues presence checking)
    └── face_presence = "detected" OR "not_detected"
        ↓
    HA Automation evaluates results:
    ├── If face detected → in_office_status = "on"
    └── If no face detected → in_office_status = "off"

User idle continues (Stage 3)
    ↓
idle_simple_lock.py
    ↓
Check in_office_status (now influenced by face detection)
    ├── "off" → Lock screen immediately (hyprlock)
    └── "on"  → Monitor continuously for status change to "off"
                ├── Status changes to "off" → Lock screen
                └── User resumes activity → Stop monitoring (exit flag)

User idle continues (Stage 4)
    ↓
idle_simple_dpms.py
    ↓
Check in_office_status (now influenced by face detection)
    ├── "off" → Turn off displays immediately (DPMS off)
    └── "on"  → Monitor continuously for status change to "off"
                ├── Status changes to "off" → Turn off displays
                └── User resumes activity → Stop monitoring (exit flag)

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
3. Stop face detection → via linux_mini_status monitoring
```

### Decision Logic

#### Face Detection Decision (Stage 2)
```
face_detector.py
    ↓
Start 1-second detection window
    ↓
Count frames with faces vs total frames
    ├── ≥50% face frames → "detected"
    │   ├── Report face_presence = "detected"
    │   └── Continue monitoring every 60s
    └── <50% face frames → Extend window by 1s (up to 10s total)
        ↓
    Final evaluation after 10s max
        ├── ≥50% → "detected" + continuous monitoring
        └── <50% → "not_detected" + stop detection

During any phase:
    └── linux_mini_status becomes "active" → Stop detection immediately
```

#### Lock Decision (Stage 3)
```
idle_simple_lock.py
    ↓
Read /tmp/mqtt/in_office_status (influenced by face detection)
    ├── "off" → Lock screen immediately (away from office OR no face detected)
    └── "on"  → Start continuous monitoring (in office OR face detected)
                    ↓
                Monitor for status change or user activity
                    ├── in_office changes to "off" → Lock screen
                    └── User activity detected (exit flag) → Stop monitoring
```

#### DPMS Decision (Stage 4)
```
idle_simple_dpms.py
    ↓
Read /tmp/mqtt/in_office_status (influenced by face detection)
    ├── "off" → DPMS off immediately (away from office OR no face detected)
    └── "on"  → Start continuous monitoring (in office OR face detected)
                    ↓
                Monitor for status change or user activity
                    ├── in_office changes to "off" → DPMS off
                    └── User activity detected (exit flag) → Stop monitoring
```

#### Continuous Monitoring
```
in_office_monitor.py (always running)
    ↓
Watch /tmp/mqtt/in_office_status for changes
    ↓
Status changed from "off" to "on"?
    └── YES → DPMS on immediately (returned to office or face detected)
```

## Dependencies

### Required Python Packages
```bash
# Core computer vision libraries
pip install opencv-python mediapipe numpy

# For the detection system
sudo pacman -S python-opencv  # Arch Linux
# OR
apt install python3-opencv    # Ubuntu/Debian
```

### System Requirements
- **Camera access**: `/dev/video0` (or primary camera device)
- **Python 3.8+**: Required for MediaPipe compatibility
- **Hyprland**: For display management integration
- **Home Assistant**: For MQTT-based office presence integration

### MediaPipe Setup
MediaPipe provides superior face detection compared to traditional cascade methods:
- **Automatic installation**: `pip install mediapipe` handles all dependencies
- **No cascade files needed**: Self-contained face mesh detection
- **GPU acceleration**: Automatically uses available GPU resources
- **Cross-platform**: Works on Linux, macOS, Windows

## Configuration

### Centralized Configuration (`config.py`)

The system now uses a centralized configuration file that eliminates hardcoded values throughout all scripts. This makes the system much easier to maintain and customize.

**Key Features:**
- **Single source of truth**: All paths, timeouts, and parameters defined in one place
- **Easy customization**: Modify behavior by editing `config.py` instead of individual scripts
- **Validation**: Built-in validation ensures required files and directories exist
- **Helper functions**: Convenient functions for accessing configuration values

**Configuration Categories:**
```python
# File paths (logs, status files, control files, device files)
LOG_FILES = {...}           # Where each script logs
STATUS_FILES = {...}        # MQTT status file locations
CONTROL_FILES = {...}       # Exit flags and control files
DEVICE_FILES = {...}        # Hardware device paths

# Timing configuration
CHECK_INTERVALS = {...}     # How often to check various conditions
FACE_DETECTION = {...}      # Face detection timing parameters
RESUME_DELAYS = {...}       # Delays for cleanup operations

# Detection parameters
DETECTION_PARAMS = {...}    # Thresholds and sensitivity settings
WEBCAM_CONFIG = {...}       # Webcam monitoring configuration

# System commands
SYSTEM_COMMANDS = {...}     # All external commands used by scripts
```

**Testing Configuration:**
```bash
# Validate configuration and check system compatibility
cd ~/.config/scripts/hyprland/idle_management
python3 config.py

# Should output:
# ✓ Created directories: /tmp/mqtt, /tmp
# ✓ Configuration validation passed
```

**Customizing Behavior:**
- **Change detection sensitivity**: Modify `DETECTION_PARAMS["threshold"]`
- **Adjust timing**: Update values in `CHECK_INTERVALS` and `FACE_DETECTION`
- **Add/remove excluded processes**: Edit `WEBCAM_CONFIG["excluded_processes"]`
- **Change file locations**: Update paths in `STATUS_FILES`, `LOG_FILES`, etc.

### Hypridle Configuration (`hypridle.conf`)
```conf
# Stage 1: report inactive status and start presence checking
listener {
    timeout = 30
    on-timeout = ~/.config/scripts/hyprland/idle_management/activity_status_reporter.py --inactive
    on-resume = ~/.config/scripts/hyprland/idle_management/idle_simple_resume.py
}

# Stage 2: face detection check
listener {
    timeout = 50
    on-timeout = ~/.config/scripts/hyprland/idle_management/face_detector.py
}

# Stage 3: check in_office and lock if off (respects face detection results)
listener {
    timeout = 60
    on-timeout = ~/.config/scripts/hyprland/idle_management/idle_simple_lock.py
}

# Stage 4: check in_office and dpms off if off (continuous monitoring)
listener {
    timeout = 90
    on-timeout = ~/.config/scripts/hyprland/idle_management/idle_simple_dpms.py
}
```

### Launch Configuration (`launch.conf`)
```conf
# Initialize idle management status files
exec-once = ~/.config/scripts/hyprland/idle_management/init_presence_status.py

# Start in-office monitor continuously
exec-once = ~/.config/scripts/hyprland/idle_management/in_office_monitor.py &
```

## Integration Points

### MQTT Integration
- **Publisher**: `mqtt_reports.py` monitors `/tmp/mqtt/` files
- **Consumer**: Home Assistant receives status updates
- **External Input**: Office status received via MQTT from motion sensors
- **Face Detection**: `face_presence` status influences `in_office_status` via HA automation
- **Webcam Filtering**: Smart filtering prevents false positives from automated camera usage

### Home Assistant Automation Required
The system requires HA automation to integrate face detection results:

```yaml
# Pseudo-code for required HA automation logic:
when idle_detection_status == "in_progress":
  wait_for_face_detection_results()

if face_presence == "detected":
  set in_office_status = "on"
elif face_presence == "not_detected":
  set in_office_status = "off"
```

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
- **Face Detection**: `/tmp/face_detector.log`
- **In-office Monitor**: `/tmp/in_office_monitor.log`
- **Simple Lock**: `/tmp/idle_simple_lock.log`
- **Simple DPMS**: `/tmp/idle_simple_dpms.log`
- **Simple Resume**: `/tmp/idle_simple_resume.log`
- **Activity Reporter**: `/tmp/mini_status_debug.log`
- **Manual Override**: `/tmp/hypridle_toggle.log`

### Comprehensive Debug Monitor
```bash
# Use the enhanced debug logger for real-time system monitoring
~/.config/scripts/hyprland/idle_management/debug/debug_idle_temp_files.py

# Provides:
# - Real-time status file change detection
# - Log file monitoring with new entry alerts
# - Control flag monitoring
# - System state analysis and summaries
# - Millisecond-precision event timestamps
```

### Manual Testing
```bash
# Validate configuration first
cd ~/.config/scripts/hyprland/idle_management
python3 config.py

# Check current status (paths from config)
cat /tmp/mqtt/linux_mini_status
cat /tmp/mqtt/idle_detection_status
cat /tmp/mqtt/face_presence
cat /tmp/mqtt/linux_webcam_status
cat /tmp/mqtt/in_office_status

# Test optimized human presence detection
python3 face_detector.py --debug

# Test activity reporting
python3 activity_status_reporter.py --active
python3 activity_status_reporter.py --inactive

# Test webcam filtering
# Start face detection, then check:
cat /tmp/mqtt/linux_webcam_status  # Should remain "inactive"

# Test presence checking phase
echo "inactive" > /tmp/mqtt/linux_mini_status
# Should trigger idle_detection_status = "in_progress"

# Monitor face detection in real-time
tail -f /tmp/face_detector.log

# Test complete idle flow
echo "inactive" > /tmp/mqtt/linux_mini_status  # Stage 1 simulation
sleep 5
~/.config/scripts/hyprland/idle_management/face_detector.py  # Stage 2 simulation
```

**Human Presence Detection Testing:**
```bash
# Test optimized human presence detection with visual debugging
~/.config/scripts/hyprland/idle_management/debug/debug_face_detector_visual.py --duration 5

# Test main detection script
~/.config/scripts/hyprland/idle_management/face_detector.py

# Monitor detection in real-time (shows which methods are working)
tail -f /tmp/face_detector.log

# Test different scenarios:
# 1. Looking at screen → Should detect via MediaPipe face mesh
# 2. Looking down at phone → Should detect via MediaPipe face mesh (excellent angle coverage)
# 3. Turned to side → Should detect via MediaPipe face mesh (468 landmark detection)
# 4. Small movements → Should detect via motion detection
# 5. Edge cases → MediaPipe handles partial occlusion, tilted heads, varied lighting

# Test user activity interruption during detection
echo "active" > /tmp/mqtt/linux_mini_status  # Should stop presence detection

# Test detection results
cat /tmp/mqtt/face_presence        # Should show "detected" or "not_detected"
cat /tmp/mqtt/idle_detection_status # Should show state progression
```

### Process Monitoring
```bash
# Check running processes
ps aux | grep -E "(in_office_monitor|face_detector)"

# Check for exit flags
ls -la /tmp/*_exit 2>/dev/null || echo "No exit flags present"

# Monitor status file changes
watch -n1 'cat /tmp/mqtt/*_status 2>/dev/null'

# Monitor specific logs
tail -f /tmp/face_detector.log
tail -f /tmp/in_office_monitor.log
tail -f /tmp/hypridle_toggle.log

# Check camera usage
lsof /dev/video0  # Should show face_detector when running

# Monitor webcam status filtering
tail -f /var/log/syslog | grep linux_webcam_status
```

## Key Features

### Advanced Detection Capabilities ✨
- **MediaPipe Face Mesh**: State-of-the-art face detection using 468 facial landmarks
- **Superior Edge Case Handling**: Excellent detection when looking down at phones, tilted heads, partial occlusion
- **All-Angle Detection**: Works from front, side, and intermediate angles
- **Motion Sensitivity**: Detects subtle movements like typing or scrolling
- **Smart Thresholds**: 50% detection rate threshold for reliable presence detection
- **Adaptive Windows**: 1-10 second detection windows with automatic extension
- **Optimized Performance**: Simplified 2-method approach for faster, more reliable detection

### Intelligence
- **Face-Based Presence Detection**: Computer vision verification before locking
- **Smart Webcam Filtering**: Distinguishes automated vs manual camera usage
- **Phased Presence Checking**: Clear "in_progress" state prevents premature office status changes
- **50% Detection Threshold**: Balanced sensitivity for reliable face detection
- **Adaptive Detection Windows**: 1-10 second detection windows with automatic extension

### Simplicity
- Clear 4-stage timeout progression with logical flow
- Minimal parallel processing complexity
- Predictable behavior and timing
- Self-contained face detection (no external dependencies)

### Centralized Configuration ⚙️
- **Single source of truth**: All settings in one `config.py` file
- **Easy customization**: Change behavior without editing multiple scripts
- **Built-in validation**: Ensures system compatibility and required files exist
- **Helper functions**: Convenient access to all configuration values
- **Maintainable**: No more hunting through scripts for hardcoded values

### Manual Control
- One-click disable/enable via waybar
- Full MQTT integration for manual overrides
- Consistent status reporting across all systems
- Logged actions for debugging and tracking

### Reliability
- **Continuous Lock Monitoring**: Locks screen as soon as office status changes to "off", regardless of timing
- **Continuous DPMS Monitoring**: Turns off displays as soon as office status changes to "off", regardless of timing
- **Clean Exit Handling**: Proper shutdown of both lock and DPMS monitoring when user activity resumes
- **No Timing Issues**: Both lock and DPMS wait for face detection results to complete before acting
- **Face Detection Integration**: Prevents locking and display shutdown when user is detected via camera
- **Shared Exit Mechanism**: Both monitoring processes stop instantly when user resumes activity

### Responsive
- Immediate display activation when returning to office
- Fast resume response (< 1 second)
- No polling delays for critical state changes
- Instant manual override response
- Real-time face detection monitoring

### Office Integration
- Respects both motion sensor AND face detection for presence
- Smart locking (only when away from office AND no face detected)
- Smart display management (context-aware with multiple inputs)
- Home Assistant automation integration for complex decision logic

## Troubleshooting

### Common Issues

**Human presence detection not working:**
- Check camera permissions: `ls -la /dev/video0`
- Verify MediaPipe installation: `python -c "import mediapipe; print('MediaPipe OK')"`
- Test camera access: `lsof /dev/video0` (should be empty when not running)
- Check detection logs: `tail -f /tmp/face_detector.log`
- Verify detection threshold: Look for detection rate logs
- Check which detection methods are available: Look for "Detection methods available" in logs
- Test visual debugging: `python debug/debug_face_detector_visual.py --duration 5`

**Webcam status false positives:**
- Check if face detector is being filtered: Look for "Ignoring face detector process" in logs
- Verify `linux_webcam_status.py` filtering logic
- Test manual: `lsof /dev/video0` should show face_detector when running
- Check webcam status: `cat /tmp/mqtt/linux_webcam_status` should stay "inactive" during face detection

**Idle detection status stuck:**
- Check if `idle_detection_status` is stuck in "in_progress"
- Verify face detection completes properly
- Ensure user activity resets status via `activity_status_reporter.py --active`
- Check for stale face detection processes: `ps aux | grep face_detector`

**Locking not working:**
- Check `/tmp/mqtt/in_office_status` file exists and has correct value
- Verify hyprlock is installed and working
- Check `idle_simple_lock.log` for errors
- Verify face detection influences office status via HA automation
- Check if presence checking phase is working correctly

**Displays not turning off:**
- Verify in_office_status is "off" when expected
- Check `idle_simple_dpms.log` for hyprctl errors
- Test manual DPMS: `hyprctl dispatch dpms off`
- Ensure face detection isn't keeping office status "on" when it should be "off"

**Office status not updating:**
- Verify MQTT connection and `mqtt_reports.py` service
- Check file permissions on `/tmp/mqtt/in_office_status`
- Ensure motion sensors are reporting to Home Assistant
- Verify Home Assistant automation integrates face detection results
- Check `face_presence` status is being published correctly

**Scripts not starting:**
- Check hypridle configuration syntax
- Verify script permissions (executable)
- Check individual script logs for errors
- Verify face detection dependencies (OpenCV, camera access)

## Home Assistant Integration Requirements

To fully utilize the advanced face detection capabilities, Home Assistant automation should be configured to:

1. **Monitor Presence Checking Phase**: Watch for `idle_detection_status = "in_progress"`
2. **Wait for Face Detection Results**: Don't change `in_office_status` while presence checking is active
3. **Integrate Face Detection**: Use `face_presence` status to influence `in_office_status` decisions
4. **Handle Multiple Inputs**: Combine motion sensor data with face detection results for intelligent presence decisions

Example automation logic needed:
```
IF idle_detection_status == "in_progress":
  WAIT for face_presence result

WHEN face_presence == "detected":
  SET in_office_status = "on"

WHEN face_presence == "not_detected" AND motion_sensor == "off":
  SET in_office_status = "off"
```
