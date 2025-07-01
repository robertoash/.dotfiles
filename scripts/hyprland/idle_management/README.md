# Optimized Idle Management System with Advanced Face Detection & Facial Recognition

A streamlined idle management system that provides reliable timeout-based locking and display management for Hyprland, with advanced MediaPipe-based face detection and **optional person-specific facial recognition**.

## System Overview

This system provides intelligent idle detection with four stages:

1. **Stage 1**: Report inactive status and start presence checking phase
2. **Stage 2**: Perform face detection (generic or person-specific) to verify user presence
3. **Stage 3**: Check office presence, lock if away from office (respects face detection)
4. **Stage 4**: Check office presence, turn off displays if away from office (continuous monitoring)
5. **Background**: Continuous monitoring to turn displays back on when returning to office (with time-based scheduling)

## Architecture

```
hypridle.conf
    ├── Stage 1: activity_status_reporter.py --inactive (starts presence checking)
    ├── Stage 2: bash -c 'pidof hyprlock || face_detector.py' (skip if already locked)
    ├── Stage 3: bash -c 'pidof hyprlock || idle_simple_lock.py' (skip if already locked)
    ├── Stage 4: idle_simple_dpms.py
    └── on-resume: idle_simple_resume.py

launch.conf
    └── startup: in_office_monitor.py (continuous background)
```

## Detection Methods

### 1. **Facial Recognition** ✨ *NEW*
- **Person-specific recognition**: Recognizes specific individuals using facial encodings
- **Reference image system**: Learns from multiple photos of the target person
- **Configurable confidence thresholds**: Adjustable security vs usability
- **Fallback support**: Can fall back to generic detection if recognition fails
- **Performance optimized**: Cached encodings for fast startup
- **Security features**: Anti-spoofing protection (optional)

### 2. **MediaPipe Face Mesh**
- State-of-the-art face detection using 468 facial landmarks
- Excellent performance for all angles, orientations, and lighting conditions
- Handles edge cases: looking down at phones, tilted heads, partial occlusion
- Works from front, side, and intermediate angles

### 3. **Motion Detection**
- Detects subtle movements like typing or scrolling
- Catches interactions MediaPipe might miss
- Optimized for office environment usage

## File Structure

```
scripts/
├── mqtt/
│   ├── mqtt_reports.py                # Status reporting to MQTT (kept separate)
│   └── mqtt_listener.py               # MQTT message handling (kept separate)
└── hyprland/
    └── idle_management/
        ├── config.py                      # 🆕 Centralized configuration (includes facial recognition)
        ├── reference_faces/               # 🆕 Reference images directory (created when enabled)
        ├── init_presence_status.py        # Boot-time status initialization
        ├── activity_status_reporter.py    # Activity status + presence checking
        ├── linux_webcam_status.py         # Webcam monitoring (filtered)
        ├── idle_simple_lock.py            # Stage 3: Lock if office status off
        ├── idle_simple_dpms.py            # Stage 4: DPMS off if office status off (continuous monitoring)
        ├── idle_simple_resume.py          # Resume: Report active, DPMS on
        ├── in_office_monitor.py           # Background: DPMS on when office status → on
        ├── face_detector.py               # 🔄 Enhanced: Facial recognition + face detection engine
        └── debug/
            └── debug_idle_temp_files.py   # Comprehensive system state monitor
```

## Script Responsibilities

#### `face_detector.py` 🔄 **Enhanced**
- **Purpose**: Advanced human presence detection with optional person-specific recognition
- **Called**: By hypridle at Stage 2 timeout
- **Detection Methods** (Configurable priority):
  1. **Facial Recognition**: Person-specific recognition using reference encodings ✨
     - Recognizes target person with configurable confidence thresholds
     - Falls back to generic detection if recognition fails (configurable)
     - Logs confidence scores and recognition quality
  2. **MediaPipe Face Mesh**: State-of-the-art face detection for all angles and lighting ✨
  3. **Motion Detection**: Detects subtle movements and user interactions ✨
- **Detection Logic**:
  - Facial recognition takes priority when enabled and reference images are available
  - Requires minimum confidence threshold for positive person recognition
  - Can fall back to generic face detection if person not recognized
  - Uses optimized detection methods simultaneously for comprehensive coverage
  - 50% threshold for human presence (≥50% = detected)
  - Adaptive detection windows: 1-10 seconds with automatic extension
  - Continuous monitoring every 60s if human presence detected
- **Status Reporting**:
  - Reports `"in_progress"` to `idle_detection_status` at start
  - Reports `"detected"` or `"not_detected"` to `face_presence`
  - Logs detailed breakdown of detection methods used
  - Logs facial recognition confidence scores when applicable
- **Smart Exit**: Monitors `linux_mini_status` for user activity
- **Logging**: Comprehensive logging with facial recognition details and confidence metrics

## Facial Recognition Configuration

### Setup and Installation

```bash
# Install facial recognition dependencies
pip install face_recognition dlib

# Note: dlib may require compilation, alternative quick install:
conda install -c conda-forge dlib
pip install face_recognition
```

### Configuration in `config.py`

```python
DETECTION_PARAMS = {
    "threshold": 0.5,  # 50% threshold for presence detection
    "fallback_settings": {
        "fallback_to_generic_detection": False,
        "max_unknown_detections_before_fallback": 3,
    },
    "facial_recognition": {
        "enabled": False,
        "priority": 1,  # Lower number = higher priority
        "reference_images_dir": IDLE_MANAGEMENT_DIR / "reference_faces",
        "tolerance": 0.6,
        "min_recognition_confidence": 0.8,
        # ... other facial recognition settings
    },
    "mediapipe_face": {
        "enabled": True,
        "priority": 2,
        "min_detection_confidence": 0.5,
        "min_tracking_confidence": 0.5,
    },
    "motion": {
        "enabled": True,
        "priority": 3,
        "min_area": 200,
    }
}
```

### Setting Up Reference Images

1. **Enable Facial Recognition**:
   ```python
   # In config.py
   DETECTION_PARAMS["facial_recognition"]["enabled"] = True
   ```

2. **Create Reference Images Directory**:
   ```bash
   mkdir -p ~/.config/scripts/hyprland/idle_management/reference_faces
   ```

3. **Add Reference Photos**:
   ```bash
   # Copy 5-10 photos of the target person
   cp ~/Photos/your_face_*.jpg ~/.config/scripts/hyprland/idle_management/reference_faces/

   # Include variety:
   # - Different lighting conditions (bright, dim, natural, artificial)
   # - Multiple angles (frontal, slight profile, looking up/down)
   # - Different expressions (neutral, smiling)
   # - With/without glasses if applicable
   # - Different times of day/seasons
   ```

4. **Test Configuration**:
   ```bash
   cd ~/.config/scripts/hyprland/idle_management
   python3 config.py
   # Should show: ✓ Configuration validation passed
   ```

5. **Test Recognition**:
   ```bash
   python3 face_detector.py --debug
   # Look for: "Facial recognition enabled with X reference encodings"
   ```

### Recognition Behavior

#### Priority and Fallback Logic
```
1. Facial Recognition (if enabled and encodings available)
   ├── Person recognized with high confidence → "detected" ✅
   ├── Person recognized with low confidence → continue to fallback methods
   └── No person/unknown person → continue to fallback methods

2. Fallback Methods (if facial recognition disabled or fallback enabled)
   ├── MediaPipe face detection → "detected" if any face found
   └── Motion detection → "detected" if movement found

3. Result: "not_detected" only if ALL methods fail
```

#### Configuration Scenarios

**Scenario 1: Maximum Security** (Only target person allowed)
```python
DETECTION_PARAMS["facial_recognition"]["enabled"] = True
DETECTION_PARAMS["facial_recognition"]["fallback_to_generic_detection"] = False
DETECTION_PARAMS["facial_recognition"]["tolerance"] = 0.5
DETECTION_PARAMS["facial_recognition"]["min_recognition_confidence"] = 0.9
```

**Scenario 2: Balanced** (Preferred person + generic detection)
```python
DETECTION_PARAMS["facial_recognition"]["enabled"] = True
DETECTION_PARAMS["facial_recognition"]["fallback_to_generic_detection"] = True
DETECTION_PARAMS["facial_recognition"]["tolerance"] = 0.6
DETECTION_PARAMS["facial_recognition"]["min_recognition_confidence"] = 0.8
```

**Scenario 3: Generic Only** (Original behavior)
```python
DETECTION_PARAMS["facial_recognition"]["enabled"] = False
DETECTION_PARAMS["facial_recognition"]["fallback_to_generic_detection"] = False
DETECTION_PARAMS["facial_recognition"]["tolerance"] = 0.6
DETECTION_PARAMS["facial_recognition"]["min_recognition_confidence"] = 0.8
```

### Facial Recognition Logging

When facial recognition is enabled, detailed logs show:

```bash
# Startup
INFO - Facial recognition enabled with X reference encodings
INFO - Detection methods available:
INFO - - Facial recognition: ✓
INFO - - MediaPipe face detection: ✓
INFO - - Motion detection: ✓

# During detection
DEBUG - Target person recognized with confidence: 0.847
DEBUG - Frame 15: Human detected via facial_recognition

# Or fallback behavior
DEBUG - Person detected but confidence too low: 0.650 < 0.800
DEBUG - Frame 15: Human detected via mediapipe_face

# Final summary
INFO - Detection breakdown: {'facial_recognition': 12, 'mediapipe_face': 3, 'motion': 0}
```

### Performance Impact

| Feature | CPU Usage | Memory | Startup Time | Notes |
|---------|-----------|---------|--------------|-------|
| Generic Detection | ~10-20% | ~50MB | ~1s | Original performance |
| + Facial Recognition | ~20-30% | ~70MB | ~2-3s | Additional 200-500ms per frame |
| Cached Encodings | Minimal | +~5MB | ~1s | Encodings cached after first run |

**Optimizations Included**:
- Face detection filters before recognition (only run recognition on detected faces)
- Encoding caching (loads once, reuses across sessions)
- Configurable model complexity (`hog` vs `cnn`)
- Jitter control for speed vs accuracy balance

### Troubleshooting Facial Recognition

**Issue: "No reference encodings loaded"**
```bash
# Check if images exist
ls -la ~/.config/scripts/hyprland/idle_management/reference_faces/
# Should show .jpg, .png, etc. files

# Check if faces are detected in reference images
python3 -c "
import face_recognition
image = face_recognition.load_image_file('reference_faces/your_photo.jpg')
encodings = face_recognition.face_encodings(image)
print(f'Found {len(encodings)} faces in image')
"
```

**Issue: "Low recognition confidence"**
```bash
# Lower the tolerance (more permissive)
# In config.py:
DETECTION_PARAMS["facial_recognition"]["tolerance"] = 0.7
DETECTION_PARAMS["facial_recognition"]["min_recognition_confidence"] = 0.7

# Or add more diverse reference images
```

**Issue: "face_recognition library not available"**
```bash
# Install face_recognition
pip install face_recognition

# If compilation fails, try conda:
conda install -c conda-forge dlib
pip install face_recognition

# Or use system packages (Ubuntu/Debian):
sudo apt install cmake libopenblas-dev liblapack-dev
pip install dlib face_recognition
```

## Detection Flow with Facial Recognition

### Enhanced Detection Decision (Stage 2)
```
face_detector.py
    ↓
Start 1-second detection window
    ↓
For each frame:
    ├── Facial Recognition enabled?
    │   ├── YES → Recognize person in frame
    │   │   ├── Target person recognized with high confidence? → DETECTED ✅
    │   │   ├── Person detected but low confidence? → Continue to fallback
    │   │   └── No person/unknown person? → Continue to fallback
    │   └── NO → Skip to fallback methods
    ├── Fallback enabled OR facial recognition disabled?
    │   ├── MediaPipe face detection → Any face detected? → DETECTED
    │   └── Motion detection → Movement detected? → DETECTED
    └── All methods failed → NOT DETECTED

Count detection rate across window:
    ├── ≥50% detection frames → "detected" + continuous monitoring
    └── <50% detection frames → Extend window by 1s (up to 10s total)

Final evaluation after 10s max:
    ├── ≥50% → "detected" + continuous monitoring
    └── <50% → "not_detected" + stop detection
```

### Configuration Impact on Behavior

| Recognition Setting | Behavior | Use Case |
|-------------------|----------|----------|
| `enabled: False` | Original generic detection (MediaPipe + motion) | Multi-user environments |
| `enabled: True, fallback: True` | Person recognition → generic detection | Preferred user + guests |
| `enabled: True, fallback: False` | Person recognition only | Single-user security |

## System Flow with Facial Recognition

### Boot Sequence
1. **Hyprland starts** → `launch.conf` executes
2. **`init_presence_status.py`** → Creates status files with defaults
3. **`in_office_monitor.py`** → Starts continuous background monitoring
4. **System ready** → Advanced idle detection with optional facial recognition active

### Enhanced Idle Detection Flow

```
User becomes idle (Stage 1)
    ↓
activity_status_reporter.py --inactive
    ↓ (writes status files)
    ├── linux_mini_status = "inactive"
    └── idle_detection_status = "in_progress" (starts presence checking phase)

User idle continues (Stage 2)
    ↓
face_detector.py (Enhanced with Facial Recognition)
    ↓ (maintains status)
    ├── idle_detection_status = "in_progress" (continues presence checking)
    └── face_presence = "detected" OR "not_detected"
        ↓ (NEW: method-specific results)
        ├── facial_recognition: Target person recognized → "detected"
        ├── mediapipe_face: Generic face found → "detected"
        ├── motion: Movement detected → "detected"
        └── none: No detection by any method → "not_detected"
        ↓
    HA Automation evaluates results:
    ├── If face detected (any method) → in_office_status = "on"
    └── If no face detected → in_office_status = "off"

User idle continues (Stage 3)
    ↓
idle_simple_lock.py
    ↓
Check in_office_status (now influenced by face detection)
    ├── "off" → Lock screen immediately (hyprlock)
    └── "on"  → Monitor continuously for status change to "off", then lock
                ├── Status changes to "off" → Lock screen
                └── User resumes activity → Stop monitoring (exit flag)

User idle continues (Stage 4)
    ↓
idle_simple_dpms.py
    ↓
Check in_office_status (now influenced by face detection)
    ├── "off" → Turn off displays immediately (DPMS off)
    └── "on"  → Monitor continuously for status change to "off", then turn off displays
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

## Key Features

### Advanced Detection Capabilities ✨
- **🆕 Facial Recognition**: Person-specific recognition with configurable security levels
- **🆕 Reference Learning**: Learns from multiple photos for robust recognition
- **🆕 Confidence Scoring**: Detailed confidence metrics and thresholds
- **🆕 Smart Fallbacks**: Graceful degradation to generic detection when needed
- **MediaPipe Face Mesh**: State-of-the-art face detection using 468 facial landmarks
- **Superior Edge Case Handling**: Excellent detection when looking down at phones, tilted heads, partial occlusion
- **All-Angle Detection**: Works from front, side, and intermediate angles
- **Motion Sensitivity**: Detects subtle movements like typing or scrolling
- **Smart Thresholds**: 50% detection rate threshold for reliable presence detection
- **Adaptive Windows**: 1-10 second detection windows with automatic extension
- **Optimized Performance**: Configurable models and caching for balanced speed vs accuracy

### Intelligence
- **🆕 Person-Specific Presence**: Recognizes specific individuals vs generic human presence
- **🆕 Configurable Security**: From generic detection to person-only recognition
- **🆕 Learning System**: Improves over time with additional reference images
- **🆕 Manual Lock Awareness**: Skips unnecessary operations when already locked
- **🆕 Race Condition Prevention**: Handles motion sensor conflicts and manual locking
- **Face-Based Presence Detection**: Computer vision verification before locking
- **Smart Webcam Filtering**: Distinguishes automated vs manual camera usage
- **Phased Presence Checking**: Clear "in_progress" state prevents premature office status changes
- **50% Detection Threshold**: Balanced sensitivity for reliable detection
- **Adaptive Detection Windows**: 1-10 second detection windows with automatic extension

### Power Management ⚡
- **🆕 Time-Based DPMS Control**: Intelligent monitor scheduling based on work hours
- **Smart Monitor Management**: Office status always turns on (lights), monitors conditionally
- **Schedule Flexibility**: Configurable work days and hours
- **Manual Override**: Keyboard/mouse activity always turns on monitors
- **Power Optimization**: Reduces unnecessary monitor usage outside work hours
- **Weekend Modes**: Different behavior for weekdays vs weekends

### Centralized Configuration ⚙️
- **🆕 Facial Recognition Settings**: Complete control over person recognition behavior
- **🆕 DPMS Scheduling**: Time-based display management configuration
- **Single source of truth**: All settings in one `config.py` file
- **Easy customization**: Change behavior without editing multiple scripts
- **Built-in validation**: Ensures system compatibility and required files exist
- **Helper functions**: Convenient access to all configuration values
- **Maintainable**: No more hunting through scripts for hardcoded values

## Dependencies

### Required Python Packages
```bash
# Core computer vision libraries
pip install opencv-python mediapipe numpy

# NEW: For facial recognition (optional)
pip install face_recognition dlib

# Alternative dlib installation if compilation fails:
conda install -c conda-forge dlib
```

### System Requirements
- **Camera access**: `/dev/video0` (or primary camera device)
- **Python 3.8+**: Required for MediaPipe compatibility
- **🆕 For facial recognition**: Additional ~1GB disk space for dlib models
- **Hyprland**: For display management integration
- **Home Assistant**: For MQTT-based office presence integration

### MediaPipe + Face Recognition Setup
```bash
# Complete installation for all features
pip install opencv-python mediapipe numpy face_recognition

# Verify installation
python3 -c "import cv2, mediapipe, face_recognition; print('All libraries installed successfully')"
```

## Configuration

### Centralized Configuration (`config.py`)

The system now includes comprehensive facial recognition configuration alongside existing settings.

**🆕 Facial Recognition Configuration:**
```python
DETECTION_PARAMS = {
    "threshold": 0.5,  # 50% threshold for presence detection
    "fallback_settings": {
        "fallback_to_generic_detection": False,
        "max_unknown_detections_before_fallback": 3,
    },
    "facial_recognition": {
        "enabled": False,
        "priority": 1,  # Lower number = higher priority
        "reference_images_dir": IDLE_MANAGEMENT_DIR / "reference_faces",
        "tolerance": 0.6,
        "min_recognition_confidence": 0.8,
        # ... other facial recognition settings
    },
    "mediapipe_face": {
        "enabled": True,
        "priority": 2,
        "min_detection_confidence": 0.5,
        "min_tracking_confidence": 0.5,
    },
    "motion": {
        "enabled": True,
        "priority": 3,
        "min_area": 200,
    }
}
```

**Testing Facial Recognition Configuration:**
```bash
# Validate complete configuration including facial recognition
cd ~/.config/scripts/hyprland/idle_management
python3 config.py

# Should output:
# ✓ Created directories: /tmp/mqtt, reference_faces
# ✓ Configuration validation passed
# Detection methods: Facial Recognition + MediaPipe + Motion
```

**Customizing Facial Recognition:**
- **Security Level**: Adjust `tolerance` and `min_recognition_confidence`
- **Performance**: Change `face_detection_model` between "hog" (fast) and "cnn" (accurate)
- **Behavior**: Enable/disable `fallback_to_generic_detection`
- **Reference Management**: Add/remove images in `reference_images_dir`

### 🆕 Time-Based DPMS Control

The system now supports intelligent monitor management based on work schedules. The `in_office` status always turns on (triggering lights and other automations), but monitor displays only auto-turn-on during configured work hours.

**DPMS Schedule Configuration (`config.py`):**
```python
DPMS_SCHEDULE = {
    "enabled": True,                    # Set to False to disable time restrictions
    "work_days": [0, 1, 2, 3, 4],      # Monday=0, Sunday=6 (weekdays only)
    "work_hours": {
        "start": "06:00",               # Work starts at 6 AM
        "end": "20:00",                 # Work ends at 8 PM
    },
}
```

**Behavior:**
- **Motion sensor triggers** → `in_office` turns "on" → **Lights turn on** ✅
- **During work hours (M-F 6AM-8PM)** → Monitors also turn on ✅
- **Outside work hours** → Monitors stay off, only lights turn on ✅
- **Manual activity (keyboard/mouse)** → Always turns monitors on regardless of time ✅

**Configuration Functions:**
- `get_dpms_schedule_config()` - Get complete schedule configuration
- `is_within_work_hours()` - Check if current time is within configured work hours

**Customization Options:**
- **Disable scheduling**: Set `enabled: False` - monitors always auto-turn-on
- **Weekend work**: Add `5, 6` to `work_days` for Saturday/Sunday
- **Different hours**: Change `start`/`end` times (24-hour format)
- **Custom days**: Modify `work_days` array (0=Monday, 6=Sunday)

**Use Cases:**
- **Night gaming**: Monitors stay off when entering room at night
- **Early morning**: Monitors stay off during early hours
- **Weekend relaxation**: Different behavior on weekends vs weekdays
- **Power saving**: Reduces unnecessary monitor usage outside work hours

## Integration Points

### 🆕 Facial Recognition Integration
- **Reference Images**: Stored in configurable directory with automatic encoding generation
- **Performance Caching**: Face encodings cached for fast startup and recognition
- **Security Levels**: From open (any face) to secure (specific person only)
- **Confidence Logging**: Detailed metrics for tuning and debugging

### MQTT Integration
- **Publisher**: `mqtt_reports.py` monitors `/tmp/mqtt/` files
- **🔄 Enhanced Status**: Face detection now includes facial recognition method details
- **Consumer**: Home Assistant receives status updates with recognition information
- **External Input**: Office status received via MQTT from motion sensors
- **Face Detection**: `face_presence` status influences `in_office_status` via HA automation

## Troubleshooting

### 🆕 Facial Recognition Issues

**Facial recognition not working:**
- Check library installation: `python -c "import face_recognition; print('OK')"`
- Verify reference images: `ls ~/.config/scripts/hyprland/idle_management/reference_faces/`
- Check encoding generation: Look for "Loaded X cached face encodings" in logs
- Test individual photos: Use debug mode to see detection details

**Low recognition confidence:**
- Add more diverse reference images (different lighting, angles, expressions)
- Lower tolerance: Change `tolerance` from 0.6 to 0.7 in config
- Lower confidence threshold: Reduce `min_recognition_confidence`
- Check image quality: Ensure clear, well-lit reference photos

**Performance issues:**
- Use "hog" model instead of "cnn": `"face_detection_model": "hog"`
- Reduce jitters: `"num_jitters": 1`
- Enable fallback: `"fallback_to_generic_detection": True`
- Add more reference images to improve accuracy (reduces computation time)

### Manual Testing
```bash
# Validate configuration first
cd ~/.config/scripts/hyprland/idle_management
python3 config.py

# Check current status (paths from config)
cat /tmp/mqtt/linux_mini_status
cat /tmp/mqtt/idle_detection_status
cat /tmp/mqtt/face_presence

# Test facial recognition specifically
python3 face_detector.py --debug
# Look for:
# - "Facial recognition enabled with X reference encodings"
# - "Target person recognized with confidence: 0.XXX"
# - Detection method breakdown in logs

# Test different scenarios:
# 1. Target person in front of camera → Should show "facial_recognition" method
# 2. Different person → Should show fallback method or "not_detected"
# 3. No person → Should show motion detection or "not_detected"

# Monitor recognition in real-time
tail -f /tmp/face_detector.log | grep -E "(recognized|confidence|Detection breakdown)"
```

## Home Assistant Integration Requirements

To fully utilize the enhanced facial recognition capabilities, Home Assistant automation should be configured to:

1. **Monitor Presence Checking Phase**: Watch for `idle_detection_status = "in_progress"`
2. **Wait for Detection Results**: Don't change `in_office_status` while presence checking is active
3. **🆕 Leverage Recognition Details**: Use facial recognition confidence and method information
4. **Integrate Detection Results**: Use `face_presence` status to influence `in_office_status` decisions
5. **Handle Multiple Inputs**: Combine motion sensor data with facial recognition results

Example automation logic:
```
IF idle_detection_status == "in_progress":
  WAIT for face_presence result

WHEN face_presence == "detected":
  IF detection_method == "facial_recognition":
    SET in_office_status = "on" (high confidence - target person present)
  ELSE:
    SET in_office_status = "on" (generic detection - someone present)

WHEN face_presence == "not_detected" AND motion_sensor == "off":
  SET in_office_status = "off"
```

**🆕 Enhanced HA Integration Ideas:**
- Different automation behavior based on recognition vs generic detection
- Confidence-based timeouts (higher confidence = longer idle timeouts)
- Person-specific settings and preferences
- Security notifications for unknown person detection

## 🔧 Configurable Detection Method Order

The face detector now supports configurable detection method ordering with flexible fallback behavior using a hierarchical configuration structure.

### Configuration Structure

In `config.py`, the `DETECTION_PARAMS` section now uses a hierarchical structure:

```python
DETECTION_PARAMS = {
    "threshold": 0.5,  # 50% threshold for presence detection
    "fallback_settings": {
        "fallback_to_generic_detection": False,
        "max_unknown_detections_before_fallback": 3,
    },
    "facial_recognition": {
        "enabled": True,
        "priority": 1,  # Lower number = higher priority
        "reference_images_dir": IDLE_MANAGEMENT_DIR / "reference_faces",
        "tolerance": 0.6,
        "min_recognition_confidence": 0.5,
        # ... other facial recognition settings
    },
    "mediapipe_face": {
        "enabled": True,
        "priority": 2,
        "min_detection_confidence": 0.5,
        "min_tracking_confidence": 0.5,
    },
    "motion": {
        "enabled": True,
        "priority": 3,
        "min_area": 200,
    }
}
```

### Priority-Based Ordering

Detection methods are automatically ordered by their `priority` value (lower number = higher priority).
Only enabled methods are included in the detection order.

### Fallback Behavior

The `fallback_to_generic_detection` parameter in `fallback_settings` controls execution:

- **`True` (Fallback Chain)**: Try methods in priority order until one succeeds
  - Example: Try facial recognition → if fails, try MediaPipe → if fails, try motion
  - Use case: Maximum detection coverage, any human presence triggers detection

- **`False` (Single Method)**: Only use the highest-priority enabled method
  - Example: If facial recognition is available, only use that method
  - Use case: Strict person-specific detection, ignore unknown faces

### Example Configurations

#### 🔐 Security-Focused (Person-Specific Only)
```python
"fallback_to_generic_detection": False,
"facial_recognition": {"enabled": True, "priority": 1},
"motion": {"enabled": True, "priority": 2},
"mediapipe_face": {"enabled": False, "priority": 3},
```
Only the recognized person triggers detection. Unknown faces are ignored.

#### 🔄 Balanced (Fallback Enabled)
```python
"fallback_to_generic_detection": True,
"facial_recognition": {"enabled": True, "priority": 1},
"mediapipe_face": {"enabled": True, "priority": 2},
"motion": {"enabled": True, "priority": 3},
```
Prefers the specific person but falls back to any human presence.

#### 🏃 Motion-First (Activity Detection)
```python
"fallback_to_generic_detection": True,
"motion": {"enabled": True, "priority": 1},
"facial_recognition": {"enabled": True, "priority": 2},
"mediapipe_face": {"enabled": True, "priority": 3},
```
Prioritizes any activity, then validates with face detection.

### Logging Output

The system logs the configured order and behavior:
```
Detection method order: facial_recognition → mediapipe_face → motion
Fallback behavior: Enabled (try all methods in order)
```
