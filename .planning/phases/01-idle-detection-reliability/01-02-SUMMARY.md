---
phase: 01-idle-detection-reliability
plan: 02
subsystem: infra
tags: [systemd, mqtt, reliability, restart-policies, network-dependencies]

# Dependency graph
requires:
  - phase: 01-01
    provides: Fixed MQTT service reconnection logic
provides:
  - Hardened systemd units with restart limits preventing permanent failures
  - Network dependency for MQTT services ensuring network-ready startup
  - Consistent restart policies across all idle detection services
affects: [infrastructure, monitoring, systemd-services]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Systemd restart limits: StartLimitIntervalSec=300 + StartLimitBurst=10 for transient failure tolerance"
    - "Network dependencies: Wants=network-online.target for MQTT services"
    - "Restart policy standardization: Restart=on-failure with RestartSec for all services"

key-files:
  created: []
  modified:
    - linuxmini/systemd/user/mqtt_listener.service
    - linuxmini/systemd/user/mqtt_reports.service
    - linuxmini/systemd/user/in-office-monitor.service
    - linuxmini/systemd/user/mqtt_linux-webcam-status.service
    - linuxmini/systemd/user/hypridle.service

key-decisions:
  - "StartLimitIntervalSec=300 / StartLimitBurst=10 allows 10 restarts in 5 minutes (vs systemd default 5 in 10s)"
  - "MQTT services now wait for network-online.target to prevent startup before network is ready"
  - "Changed webcam service from Restart=always to Restart=on-failure to respect clean exits"

patterns-established:
  - "All idle detection services use consistent restart limits (300s interval, 10 burst)"
  - "Network-dependent services explicitly wait for network-online.target"

# Metrics
duration: ~15min
completed: 2026-02-12
---

# Phase 01 Plan 02: Systemd Hardening Summary

**All idle detection systemd units hardened with restart limits (10 restarts in 5 minutes) and network dependencies, preventing permanent service failures after transient issues**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-02-12 (estimated)
- **Completed:** 2026-02-12T19:14:39Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- All five idle detection services now have StartLimitIntervalSec=300 and StartLimitBurst=10, allowing them to survive transient failures without hitting systemd's overly aggressive default restart limits
- MQTT services (mqtt_listener and mqtt_reports) now wait for network-online.target before starting, preventing immediate failures when network isn't ready
- Webcam status service changed from Restart=always to Restart=on-failure, respecting clean exits instead of restarting forever

## Task Commits

Each task was committed atomically:

1. **Task 1: Harden MQTT service units with restart policies and network dependencies** - `c75b9a0` (feat)
2. **Task 2: Harden remaining idle detection service units** - `212cc6a` (feat)
3. **Task 3: Deploy and verify all services are running** - (checkpoint:human-verify - user verified services running correctly)

## Files Created/Modified
- `linuxmini/systemd/user/mqtt_listener.service` - Added network-online.target dependency and restart limits
- `linuxmini/systemd/user/mqtt_reports.service` - Added network-online.target dependency and restart limits
- `linuxmini/systemd/user/in-office-monitor.service` - Added restart limits
- `linuxmini/systemd/user/mqtt_linux-webcam-status.service` - Changed to Restart=on-failure, added RestartSec=5 and restart limits
- `linuxmini/systemd/user/hypridle.service` - Added restart limits

## Decisions Made

**StartLimitIntervalSec=300 / StartLimitBurst=10**: Allows 10 restarts in 5 minutes before systemd gives up, much more forgiving than the default (5 restarts in 10 seconds). This prevents permanent service failures from transient issues like temporary network drops or brief MQTT broker unavailability.

**network-online.target dependency for MQTT services**: Ensures MQTT services don't start until the network is actually ready, preventing immediate failure loops at boot or after network disconnections.

**webcam service Restart=on-failure instead of Restart=always**: The original Restart=always would restart even on clean exit (exit code 0), which is unnecessary and could cause rapid restart loops. on-failure is more appropriate.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - all tasks completed without issues. User verified services running and communicating correctly after deployment.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

All idle detection services now have production-grade restart policies and network dependencies. Services can survive:
- Temporary network failures (MQTT services wait for network)
- Brief MQTT broker unavailability (restart limits allow recovery)
- Process crashes (automatic restart with backoff)

The idle detection system is now hardened against transient failures. Ready for ongoing monitoring and any future reliability improvements.

## Self-Check: PASSED

All files verified:
- FOUND: linuxmini/systemd/user/mqtt_listener.service
- FOUND: linuxmini/systemd/user/mqtt_reports.service
- FOUND: linuxmini/systemd/user/in-office-monitor.service
- FOUND: linuxmini/systemd/user/mqtt_linux-webcam-status.service
- FOUND: linuxmini/systemd/user/hypridle.service

All commits verified:
- FOUND: c75b9a0
- FOUND: 212cc6a

---
*Phase: 01-idle-detection-reliability*
*Completed: 2026-02-12*
