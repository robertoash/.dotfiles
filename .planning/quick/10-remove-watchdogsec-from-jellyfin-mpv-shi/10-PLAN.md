---
phase: quick-10
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - linuxmini/systemd/user/jellyfin-mpv-shim.service
autonomous: true
must_haves:
  truths:
    - "WatchdogSec is no longer present in the jellyfin-mpv-shim service file"
    - "Service retains all other resilience layers (Restart=always, RestartSec, StartLimitBurst, StartLimitIntervalSec)"
    - "Systemd user daemon is reloaded and service restarted cleanly"
  artifacts:
    - path: "linuxmini/systemd/user/jellyfin-mpv-shim.service"
      provides: "Service unit without WatchdogSec"
      contains: "Restart=always"
  key_links: []
---

<objective>
Remove WatchdogSec=600 from the jellyfin-mpv-shim systemd service unit.

Purpose: jellyfin-mpv-shim does not implement the systemd watchdog protocol (sd_notify WATCHDOG=1). When WatchdogSec is set but the app never sends watchdog notifications, systemd kills the process after the timeout period. This causes the service to be killed during normal health check operations.

Output: Updated service file without WatchdogSec, daemon reloaded, service restarted.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@linuxmini/systemd/user/jellyfin-mpv-shim.service
</context>

<tasks>

<task type="auto">
  <name>Task 1: Remove WatchdogSec and reload service</name>
  <files>linuxmini/systemd/user/jellyfin-mpv-shim.service</files>
  <action>
Remove the `WatchdogSec=600` line from the [Service] section of `linuxmini/systemd/user/jellyfin-mpv-shim.service`.

Keep all other directives intact:
- Type=simple
- ExecStartPre=/usr/bin/sleep 3
- ExecStart=/usr/bin/jellyfin-mpv-shim
- Restart=always
- RestartSec=15

After editing the source file, run `cd /home/rash/.dotfiles && python setup.py` to apply the symlink (should already be linked, but ensures consistency).

Then reload the systemd user daemon and restart the service:
```
systemctl --user daemon-reload
systemctl --user restart jellyfin-mpv-shim.service
```
  </action>
  <verify>
1. `grep WatchdogSec linuxmini/systemd/user/jellyfin-mpv-shim.service` returns nothing
2. `systemctl --user show jellyfin-mpv-shim.service -p WatchdogUSec` shows `WatchdogUSec=0` (disabled)
3. `systemctl --user is-active jellyfin-mpv-shim.service` shows `active`
  </verify>
  <done>WatchdogSec removed from service file, systemd daemon reloaded, service running without watchdog enforcement</done>
</task>

</tasks>

<verification>
- Service file has no WatchdogSec line
- Service is active and not being killed by watchdog
- All other resilience layers remain (Restart=always, RestartSec=15, StartLimitBurst=5, StartLimitIntervalSec=300)
</verification>

<success_criteria>
jellyfin-mpv-shim service runs without being killed by systemd watchdog timeout during health check operations
</success_criteria>

<output>
After completion, create `.planning/quick/10-remove-watchdogsec-from-jellyfin-mpv-shi/10-SUMMARY.md`
</output>
