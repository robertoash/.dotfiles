# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-10)

**Core value:** Any machine can be configured identically with one command. All configuration is declarative and versioned.
**Current focus:** Phase 1 - idle_detection_reliability

## Current Position

Phase: 1 of 1 (idle_detection_reliability)
Plan: 2 of 2 in current phase
Status: Complete
Last activity: 2026-02-12 - Completed Phase 01 Plan 02: Systemd Hardening

Progress: [##########] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 8.5 minutes
- Total execution time: 0.28 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-idle-detection-reliability | 2 | 1018s | 509s |

**Recent Trend:**
- Last 5 plans: 509s average
- Trend: Phase complete

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 01-01]: Use paho-mqtt's built-in reconnection instead of custom safe_reconnect() logic
- [Phase 01-01]: Rely on will message for offline status instead of publishing in on_disconnect
- [Phase 01-01]: Treat disconnect rc as integer for paho-mqtt 1.6.x compatibility
- [Phase quick-1]: Display downloaded amount in same unit as total size for consistency with yt-dlp output
- [Phase quick-2]: Status column width 6 (not 4) to avoid truncating header text
- [Phase quick-3]: Use --print-to-file %(height)s to extract actual resolution rather than parsing verbose output
- [Phase quick-6]: Multi-layered resilience: app-level retry (connect_retry_mins=5) + faster health checks (120s) + systemd Restart=always + WatchdogSec=600 for comprehensive recovery from websocket drops and server restarts
- [Phase 01-02]: StartLimitIntervalSec=300 / StartLimitBurst=10 allows 10 restarts in 5 minutes (vs systemd default 5 in 10s)
- [Phase 01-02]: MQTT services now wait for network-online.target to prevent startup before network is ready
- [Phase 01-02]: Changed webcam service from Restart=always to Restart=on-failure to respect clean exits

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

### Roadmap Evolution

- Phase 1 added: idle_detection_reliability

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Display memory usage in human-readable format (e.g., 512MB/2.5G) instead of percentage in down_d | 2026-02-11 | 8b02b94 | [1-display-memory-usage-in-human-readable-f](./quick/1-display-memory-usage-in-human-readable-f/) |
| 2 | Add quality column (720p/1080p/1440p/2160p) to down_d progress table | 2026-02-11 | c8a7e16 | [2-add-quality-column-720p-1080p-1440p-2160](./quick/2-add-quality-column-720p-1080p-1440p-2160/) |
| 3 | Parse actual video quality from yt-dlp output instead of showing requested quality | 2026-02-11 | c89ed15 | [3-parse-actual-video-quality-from-yt-dlp-o](./quick/3-parse-actual-video-quality-from-yt-dlp-o/) |
| 4 | Review and fix laggy dot expansion implementation | 2026-02-11 | c547881 | [4-dotfiles-yks](./quick/4-dotfiles-yks/) |
| 5 | Fix border colors for pinned and sneaky windows to show correct solid colors on focus/unfocus state changes | 2026-02-12 | 8b483e3 | [5-fix-border-colors-for-pinned-and-sneaky-](./quick/5-fix-border-colors-for-pinned-and-sneaky-/) |
| 6 | Fix jellyfin-mpv-shim websocket errors and harden service against connection issues | 2026-02-12 | a3c552c | [6-fix-jellyfin-mpv-shim-websocket-errors-a](./quick/6-fix-jellyfin-mpv-shim-websocket-errors-a/) |
| 7 | Implement priority-based bluetooth audio switching with automated daemon | 2026-02-12 | 6c11c20 | [7-implement-priority-based-bluetooth-audio](./quick/7-implement-priority-based-bluetooth-audio/) |

## Session Continuity

Last session: 2026-02-12
Stopped at: Completed Phase 01 Plan 02 (Systemd Hardening)
Resume file: None
