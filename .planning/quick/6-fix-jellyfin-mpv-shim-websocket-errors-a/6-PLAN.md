---
phase: quick-6
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - linuxmini/config/jellyfin-mpv-shim/conf.json
  - common/config/jellyfin-mpv-shim/conf.json
  - linuxmini/systemd/user/jellyfin-mpv-shim.service
autonomous: true

must_haves:
  truths:
    - "jellyfin-mpv-shim auto-recovers from websocket drops without manual restart"
    - "jellyfin-mpv-shim auto-recovers from Jellyfin server restarts"
    - "systemd watchdog restarts the service if it gets into a stuck state"
  artifacts:
    - path: "linuxmini/config/jellyfin-mpv-shim/conf.json"
      provides: "App-level reconnection config"
      contains: "connect_retry_mins"
    - path: "common/config/jellyfin-mpv-shim/conf.json"
      provides: "Common reconnection config"
      contains: "connect_retry_mins"
    - path: "linuxmini/systemd/user/jellyfin-mpv-shim.service"
      provides: "Service-level restart guardrails"
      contains: "WatchdogSec"
  key_links:
    - from: "linuxmini/systemd/user/jellyfin-mpv-shim.service"
      to: "systemd watchdog"
      via: "WatchdogSec + Restart=always"
      pattern: "WatchdogSec|Restart=always"
---

<objective>
Fix jellyfin-mpv-shim websocket "socket is closed" errors and harden the service against future connection issues.

Purpose: The service experiences recurring websocket disconnections (especially during Jellyfin server restarts or network hiccups) and the upstream jellyfin-apiclient-python ws_client.py has a known bug where the reconnection loop exits immediately instead of retrying. While we cannot fix the upstream bug, we can: (1) enable the app's built-in retry mechanism via `connect_retry_mins`, (2) lower the health check interval so stale connections are detected faster, and (3) harden the systemd service with `Restart=always` + watchdog so it recovers from any stuck state.

Output: Updated config files and service unit, service restarted and healthy.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

Key analysis of the problem:
- The websocket "socket is closed" errors come from jellyfin_apiclient_python/ws_client.py
- The ws_client.py run() method has a broken reconnect loop: `if not self.stop: break` exits
  instead of reconnecting when the socket drops unexpectedly
- However, jellyfin-mpv-shim's clients.py has its own reconnect logic in setup_client() that
  handles WebSocketDisconnect events with exponential backoff (expo(100)) -- this works correctly
- The app-level `connect_retry_mins: 0` means initial connection failures are not retried
- The `health_check_interval: 300` (5 min) means stale connections take up to 5 minutes to detect
- The systemd service uses `Restart=on-failure` which only restarts on non-zero exit, not on
  stuck/degraded states
- The 500 Server Error flood on Feb 8 04:06-05:41 was during a Jellyfin server restart; the
  service kept hammering the server every 5 minutes via health checks
- The Feb 12 22:22 websocket errors occurred during active media playback

Config files: conf.json exists in both common/ and linuxmini/ in dotfiles but is NOT symlinked
to ~/.config/ -- jellyfin-mpv-shim writes it directly. The dotfiles copies must be updated to
stay in sync, and setup.py copies them. Both copies must be modified.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update jellyfin-mpv-shim config for faster reconnection</name>
  <files>
    linuxmini/config/jellyfin-mpv-shim/conf.json
    common/config/jellyfin-mpv-shim/conf.json
  </files>
  <action>
In both conf.json files, make these changes:

1. Set `"connect_retry_mins": 5` (was 0). This enables the app's built-in retry loop that
   attempts reconnection every 30 seconds for up to 5 minutes on initial connection failure.
   This handles Jellyfin server restarts gracefully.

2. Set `"health_check_interval": 120` (was 300). This reduces stale connection detection time
   from 5 minutes to 2 minutes. The health check calls validate_client() which detects if the
   client is no longer registered with the server and triggers reconnection via WebSocketDisconnect.

Also copy the updated linuxmini conf.json to the live location at ~/.config/jellyfin-mpv-shim/conf.json
so the changes take effect on next service restart (the app reads conf.json on startup, so
the file must be in place before restarting).
  </action>
  <verify>
Verify both dotfiles conf.json files have the updated values:
- `grep connect_retry_mins linuxmini/config/jellyfin-mpv-shim/conf.json` shows 5
- `grep health_check_interval linuxmini/config/jellyfin-mpv-shim/conf.json` shows 120
- Same for common/config/jellyfin-mpv-shim/conf.json
- `grep connect_retry_mins ~/.config/jellyfin-mpv-shim/conf.json` shows 5
  </verify>
  <done>Both dotfiles copies and live config have connect_retry_mins=5 and health_check_interval=120</done>
</task>

<task type="auto">
  <name>Task 2: Harden systemd service with Restart=always and watchdog</name>
  <files>linuxmini/systemd/user/jellyfin-mpv-shim.service</files>
  <action>
Update the systemd service unit at linuxmini/systemd/user/jellyfin-mpv-shim.service:

1. Change `Restart=on-failure` to `Restart=always`. The on-failure policy only triggers on
   non-zero exit codes. If the process gets stuck (websocket dead, no health check recovery),
   it stays running but useless. `Restart=always` combined with watchdog catches more failure modes.

2. Add `RestartSec=15` (was 10). Slightly longer backoff gives the Jellyfin server time to
   stabilize after a restart before the shim tries to reconnect.

3. Add `WatchdogSec=600` (10 minutes). If the process becomes unresponsive, systemd will
   kill and restart it. jellyfin-mpv-shim does not natively support sd_notify watchdog pings,
   but WatchdogSec with Type=simple means systemd will use process liveness checks. Note:
   with Type=simple, WatchdogSec relies on the process not being a zombie; this provides
   a safety net for hard hangs.

4. Add `StartLimitIntervalSec=300` and `StartLimitBurst=5` to the [Unit] section to prevent
   restart loops -- max 5 restarts in 5 minutes before systemd gives up.

5. Remove `ExecStartPre=/bin/sleep 5`. Instead add `ExecStartPre=/usr/bin/sleep 3` -- slightly
   shorter sleep is fine since we now have connect_retry_mins for connection retry.

Then run `cd ~/.dotfiles && python setup.py` to deploy the symlink, then
`systemctl --user daemon-reload && systemctl --user restart jellyfin-mpv-shim.service` to apply.
  </action>
  <verify>
- `systemctl --user cat jellyfin-mpv-shim.service` shows Restart=always, WatchdogSec=600, RestartSec=15, StartLimitBurst=5
- `systemctl --user status jellyfin-mpv-shim.service` shows active (running)
- Wait 30 seconds, then `journalctl --user -u jellyfin-mpv-shim.service --no-pager -n 10` shows
  healthy startup with no immediate errors
  </verify>
  <done>Service unit has Restart=always, watchdog, and rate limiting. Service is running and healthy after restart.</done>
</task>

</tasks>

<verification>
After both tasks:
1. `systemctl --user status jellyfin-mpv-shim.service` shows active (running)
2. `journalctl --user -u jellyfin-mpv-shim.service --no-pager -n 20` shows clean startup, health checks running at ~2 min intervals
3. No "socket is closed" errors in fresh logs (note: these may still occur during server restarts, but the service will now recover automatically)
</verification>

<success_criteria>
- jellyfin-mpv-shim service is running with hardened systemd config
- Config enables 5-minute connection retry and 2-minute health checks
- Systemd will auto-restart the service on any exit (not just failure)
- Restart rate limiting prevents restart loops
- Both dotfiles copies and live config are in sync
</success_criteria>

<output>
After completion, create `.planning/quick/6-fix-jellyfin-mpv-shim-websocket-errors-a/6-SUMMARY.md`
</output>
