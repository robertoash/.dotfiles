# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-10)

**Core value:** Any machine can be configured identically with one command. All configuration is declarative and versioned.
**Current focus:** Phase 2 - fish-tab-autocomplete-robustness

## Current Position

Phase: 2 of 2 (fish-tab-autocomplete-robustness)
Plan: 3 of 4 in current phase
Status: In Progress
Last activity: 2026-02-13 - Completed 02-03-PLAN.md: Smart Tab handler with ordering and preview

Progress: [#######---] 75%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 5.5 minutes
- Total execution time: 0.37 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-idle-detection-reliability | 2 | 1018s | 509s |
| 02-fish-tab-autocomplete-robustness | 2 | 184s | 92s |

**Recent Trend:**
- Last 5 plans: 295s average
- Trend: Phase 02 in progress (3/4 plans complete)

*Updated after each plan completion*
| Phase quick-10 P01 | 49 | 1 tasks | 1 files |
| Phase 02-fish-tab-autocomplete-robustness P02 | 50 | 1 tasks | 1 files |
| Phase 02 P03 | 134 | 3 tasks | 3 files |

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
- [Phase quick-8]: Use ConditionEnvironment to prevent pypr startup before Hyprland
- [Phase quick-8]: Use Restart=always instead of on-failure for pypr (exits with code 0 on error)
- [Phase quick-8]: Use systemctl restart instead of start for idempotent pypr activation in launch.conf
- [Phase quick-10]: Removed WatchdogSec=600 because jellyfin-mpv-shim doesn't implement sd_notify watchdog protocol
- [Phase quick-11]: Use --no-sort to preserve zoxide priority ordering in fzf
- [Phase quick-11]: Use ANSI yellow for Last dir highlighting, strip codes after selection
- [Phase quick-11]: Filter out PWD and __last_working_dir from zoxide list to avoid duplicates
- [Phase 02-02]: Silent failure on auth issues - completion returns nothing instead of showing errors
- [Phase 02-02]: 2-second timeout for aggressive responsiveness (Tab must feel instant)
- [Phase 02-02]: No caching in v1 - timeout keeps it fast enough, caching adds complexity
- [Phase 02-02]: StrictHostKeyChecking=accept-new for new hosts (prevents prompts, still rejects changed keys)
- [Phase 02-03]: Reasoning labels visible in fzf (--with-nth 1,2) so users see why items appear
- [Phase 02-03]: Preview hidden by default to avoid performance impact (toggle with Ctrl+P)
- [Phase 02-03]: Unknown commands get files only (more useful than both files+dirs)
- [Phase 02-03]: fzf search only in path (--nth 1) so query doesn't match labels

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

### Roadmap Evolution

- Phase 1 added: idle_detection_reliability
- Phase 2 added: fish +Tab autocomplete robustness

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 1 | Display memory usage in human-readable format (e.g., 512MB/2.5G) instead of percentage in down_d | 2026-02-11 | 8b02b94 | [1-display-memory-usage-in-human-readable-f](./quick/1-display-memory-usage-in-human-readable-f/) |
| 2 | Add quality column (720p/1080p/1440p/2160p) to down_d progress table | 2026-02-11 | c8a7e16 | [2-add-quality-column-720p-1080p-1440p-2160](./quick/2-add-quality-column-720p-1080p-1440p-2160/) |
| 3 | Parse actual video quality from yt-dlp output instead of showing requested quality | 2026-02-11 | c89ed15 | [3-parse-actual-video-quality-from-yt-dlp-o](./quick/3-parse-actual-video-quality-from-yt-dlp-o/) |
| 4 | Review and fix laggy dot expansion implementation | 2026-02-11 | c547881 | [4-dotfiles-yks](./quick/4-dotfiles-yks/) |
| 5 | Fix border colors for pinned and sneaky windows to show correct solid colors on focus/unfocus state changes | 2026-02-12 | 8b483e3 | [5-fix-border-colors-for-pinned-and-sneaky-](./quick/5-fix-border-colors-for-pinned-and-sneaky-/) |
| 6 | Fix jellyfin-mpv-shim websocket errors and harden service against connection issues | 2026-02-12 | a3c552c | [6-fix-jellyfin-mpv-shim-websocket-errors-a](./quick/6-fix-jellyfin-mpv-shim-websocket-errors-a/) |
| 7 | Implement priority-based bluetooth audio switching with automated daemon | 2026-02-12 | ca480ab | [7-implement-priority-based-bluetooth-audio](./quick/7-implement-priority-based-bluetooth-audio/) |
| 8 | Fix pypr daemon connectivity issue in Hyprland with ConditionEnvironment and Restart=always | 2026-02-12 | 54d4a2b | [8-fix-pypr-daemon-connectivity-in-hyprland](./quick/8-fix-pypr-daemon-connectivity-in-hyprland/) |
| 10 | Remove WatchdogSec from jellyfin-mpv-shim service | 2026-02-12 | 8345688 | [10-remove-watchdogsec-from-jellyfin-mpv-shi](./quick/10-remove-watchdogsec-from-jellyfin-mpv-shi/) |
| 11 | Integrate fuzzy search into bare cd function with fzf picker | 2026-02-13 | 7d92bb0 | [11-integrating-fuzzy-search-into-my-cd-func](./quick/11-integrating-fuzzy-search-into-my-cd-func/) |

## Session Continuity

Last session: 2026-02-13
Stopped at: Completed 02-03-PLAN.md: Smart Tab handler with ordering and preview
Resume file: None
