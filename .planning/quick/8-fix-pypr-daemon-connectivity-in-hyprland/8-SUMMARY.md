---
phase: quick-8
plan: 01
subsystem: hyprland/systemd
tags: [pypr, systemd, hyprland, service-management, scratchpads]
dependency_graph:
  requires:
    - HYPRLAND_INSTANCE_SIGNATURE environment variable
    - graphical-session.target
  provides:
    - Reliable pypr daemon connectivity to Hyprland
    - Auto-recovery from pypr crashes
  affects:
    - Zoom keybind (SUPER+Z)
    - Blueman scratchpad functionality
tech_stack:
  added: []
  patterns:
    - ConditionEnvironment for service activation gating
    - PassEnvironment for systemd environment inheritance
    - Restart=always for processes with zero-exit-on-error
    - systemctl restart for idempotent service initialization
key_files:
  created: []
  modified:
    - linuxmini/systemd/user/pypr.service
    - linuxmini/config/hypr/launch.conf
decisions:
  - Use ConditionEnvironment to prevent pypr startup before Hyprland
  - Use Restart=always instead of on-failure (pypr exits with code 0 on error)
  - Use systemctl restart instead of start for idempotent activation
  - Split pypr from other services in launch.conf for different restart behavior
metrics:
  duration: 76s
  tasks_completed: 2
  files_modified: 2
  commits: 2
  completed: 2026-02-12T21:56:14Z
---

# Quick Task 8: Fix Pypr Daemon Connectivity in Hyprland

**One-liner:** Pypr now starts reliably after Hyprland with ConditionEnvironment gating, PassEnvironment for socket access, and Restart=always for zero-exit-code crash recovery.

## Objective

Fixed pypr daemon failing to connect to Hyprland after boot with "No supported environment detected" error. The service previously started too early (via default.target before Hyprland), didn't restart on failure (pypr exits with code 0), and launch.conf's `systemctl start` was a no-op for previously-activated services.

## Tasks Completed

### Task 1: Fix pypr.service for Hyprland environment and resilient restarts

**Changes:**
- Added `ConditionEnvironment=HYPRLAND_INSTANCE_SIGNATURE` to prevent service activation before Hyprland sets the environment variable
- Added `PassEnvironment=HYPRLAND_INSTANCE_SIGNATURE` to inherit Hyprland socket identifier from systemd manager
- Changed `Restart=on-failure` to `Restart=always` because pypr exits with code 0 even on RuntimeError
- Changed `WantedBy=default.target` to `WantedBy=graphical-session.target` to prevent premature activation
- Added `StartLimitIntervalSec=300` and `StartLimitBurst=10` for crash loop protection (allows 10 restarts in 5 minutes)

**Result:** Service won't start until Hyprland is running, has correct environment for socket connectivity, and recovers from crashes regardless of exit code.

**Commit:** 99dbeaf

### Task 2: Fix launch.conf to use restart instead of start for pypr

**Changes:**
- Split pypr.service from the shared service start line
- Changed `systemctl --user start pypr.service` to `systemctl --user restart pypr.service`

**Rationale:** When a service exits successfully (Result=success), `systemctl start` is a no-op because systemd considers it already activated. Using `restart` forces a fresh start with the now-available Hyprland environment variables.

**Result:** Pypr gets a clean activation every time Hyprland launches, even if the service was previously started and exited.

**Commit:** 54d4a2b

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All success criteria met:

1. ✅ `systemctl --user status pypr.service` shows Active: active (running)
2. ✅ `pypr zoom ++0.5` works (confirms socket connectivity)
3. ✅ `pypr zoom` resets zoom (confirms bidirectional communication)
4. ✅ Service file has all required directives:
   - Restart=always
   - PassEnvironment=HYPRLAND_INSTANCE_SIGNATURE
   - ConditionEnvironment=HYPRLAND_INSTANCE_SIGNATURE
   - WantedBy=graphical-session.target
   - StartLimitIntervalSec=300
   - StartLimitBurst=10
5. ✅ launch.conf has `restart pypr.service` on separate line

## Technical Details

**Root cause analysis:**

1. **Environment timing:** pypr needs `HYPRLAND_INSTANCE_SIGNATURE` to connect to Hyprland's socket. The service was starting via `default.target` before Hyprland ran `systemctl --user import-environment HYPRLAND_INSTANCE_SIGNATURE`.

2. **Zero-exit-on-error:** pypr exits with code 0 even when failing with RuntimeError, so `Restart=on-failure` never triggered.

3. **Systemd activation state:** After the failed startup, systemd marked the service as `Result=success`, making `systemctl start` in launch.conf a no-op.

**Solution pattern:**

- **ConditionEnvironment:** Gates service activation until the required environment variable exists
- **PassEnvironment:** Inherits the environment variable from systemd manager to service process
- **Restart=always:** Ensures recovery regardless of exit code
- **systemctl restart:** Idempotent command that works even on previously-activated services

This pattern matches the working configuration of hypridle.service, which also requires HYPRLAND_INSTANCE_SIGNATURE.

## Self-Check: PASSED

**Created files:** None (modifications only)

**Modified files:**
```bash
FOUND: linuxmini/systemd/user/pypr.service
FOUND: linuxmini/config/hypr/launch.conf
```

**Commits:**
```bash
FOUND: 99dbeaf
FOUND: 54d4a2b
```
