---
phase: quick-6
plan: 01
subsystem: infra
tags: [jellyfin-mpv-shim, systemd, websocket, service-management, connection-resilience]

# Dependency graph
requires: []
provides:
  - Hardened jellyfin-mpv-shim service with automatic reconnection and recovery
  - Faster connection detection (2 min vs 5 min health checks)
  - 5-minute connection retry on server restarts
  - Systemd watchdog and restart guardrails
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Systemd service hardening with Restart=always and WatchdogSec for resilience"
    - "Application-level connection retry via connect_retry_mins"

key-files:
  created: []
  modified:
    - linuxmini/config/jellyfin-mpv-shim/conf.json
    - common/config/jellyfin-mpv-shim/conf.json
    - linuxmini/systemd/user/jellyfin-mpv-shim.service

key-decisions:
  - "Set connect_retry_mins=5 to retry connections for up to 5 minutes during Jellyfin server restarts"
  - "Reduced health_check_interval from 300s to 120s for faster stale connection detection"
  - "Changed Restart=on-failure to Restart=always to catch more failure modes including stuck states"
  - "Added WatchdogSec=600 for automatic restart on unresponsive process"
  - "Added StartLimitBurst=5 and StartLimitIntervalSec=300 to prevent restart loops"

patterns-established:
  - "Service resilience pattern: Combine app-level retry (connect_retry_mins) with service-level restart (Restart=always + WatchdogSec) for comprehensive recovery"

# Metrics
duration: 1min 44sec
completed: 2026-02-12
---

# Quick Task 6: Fix jellyfin-mpv-shim Websocket Errors Summary

**Hardened jellyfin-mpv-shim with automatic reconnection (5-min retry), faster health checks (2-min interval), and systemd watchdog for complete resilience against websocket drops and server restarts**

## Performance

- **Duration:** 1 minute 44 seconds
- **Started:** 2026-02-12T21:31:27Z
- **Completed:** 2026-02-12T21:33:11Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Enabled app-level connection retry (5 minutes) to handle Jellyfin server restarts gracefully
- Reduced health check interval from 5 minutes to 2 minutes for faster stale connection detection
- Hardened systemd service with Restart=always and WatchdogSec=600 to recover from stuck states
- Added restart rate limiting to prevent restart loops while maintaining resilience

## Task Commits

Each task was committed atomically:

1. **Task 1: Update jellyfin-mpv-shim config for faster reconnection** - `5578763` (chore)
2. **Task 2: Harden systemd service with restart policy and watchdog** - `a3c552c` (chore)

## Files Created/Modified
- `linuxmini/config/jellyfin-mpv-shim/conf.json` - Set connect_retry_mins=5, health_check_interval=120
- `common/config/jellyfin-mpv-shim/conf.json` - Same config updates for common baseline
- `linuxmini/systemd/user/jellyfin-mpv-shim.service` - Restart=always, WatchdogSec=600, StartLimitBurst=5, RestartSec=15

## Decisions Made
- **connect_retry_mins=5**: Enables app's built-in reconnection loop that retries every 30 seconds for up to 5 minutes on initial connection failure. This gracefully handles Jellyfin server restarts without manual intervention.
- **health_check_interval=120**: Reduced from 300s (5 min) to 120s (2 min). Health checks detect stale connections and trigger reconnection via WebSocketDisconnect event. Faster detection means quicker recovery.
- **Restart=always**: Changed from on-failure to always. The on-failure policy only triggers on non-zero exit codes. If the process gets stuck with a dead websocket (stays running but useless), on-failure won't help. Restart=always catches more failure modes.
- **WatchdogSec=600**: 10-minute watchdog timeout. If the process becomes completely unresponsive (hard hang), systemd will kill and restart it. Provides a safety net for the worst-case scenario.
- **StartLimitBurst=5 + StartLimitIntervalSec=300**: Max 5 restarts in 5 minutes before systemd gives up. Prevents infinite restart loops while allowing legitimate recovery attempts.
- **RestartSec=15**: Increased from 10s to 15s. Gives the Jellyfin server more time to stabilize after a restart before the shim tries to reconnect.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - configuration changes applied cleanly. Service restarted successfully with websocket connection established. Minor pre-existing issue with pystray module (system tray) noted but unrelated to websocket functionality.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Service is now hardened against:
- Websocket disconnections during active playback (recovers via health checks in 2 min)
- Jellyfin server restarts (retries connection for 5 minutes)
- Process hangs or stuck states (systemd watchdog restarts after 10 min)
- Restart loops (rate limiting prevents infinite restarts)

The multi-layered approach (app-level retry + health checks + systemd restart + watchdog) provides comprehensive resilience. Monitoring recommended after first Jellyfin server restart to verify recovery behavior.

---
*Phase: quick-6*
*Completed: 2026-02-12*

## Self-Check: PASSED

All files and commits verified:
- ✓ linuxmini/config/jellyfin-mpv-shim/conf.json
- ✓ common/config/jellyfin-mpv-shim/conf.json
- ✓ linuxmini/systemd/user/jellyfin-mpv-shim.service
- ✓ Commit 5578763 (Task 1)
- ✓ Commit a3c552c (Task 2)
