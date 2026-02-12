---
phase: quick-8
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - linuxmini/systemd/user/pypr.service
  - linuxmini/config/hypr/launch.conf
autonomous: true

must_haves:
  truths:
    - "Pypr starts reliably after Hyprland is initialized on every boot"
    - "Pypr restarts automatically if it crashes or exits unexpectedly"
    - "Pypr zoom and scratchpad keybinds work after boot without manual intervention"
  artifacts:
    - path: "linuxmini/systemd/user/pypr.service"
      provides: "Resilient pypr systemd service"
      contains: "Restart=always"
    - path: "linuxmini/config/hypr/launch.conf"
      provides: "Hyprland launch configuration with proper pypr startup"
  key_links:
    - from: "linuxmini/config/hypr/launch.conf"
      to: "pypr.service"
      via: "systemctl --user restart pypr.service"
      pattern: "systemctl.*pypr"
    - from: "linuxmini/systemd/user/pypr.service"
      to: "HYPRLAND_INSTANCE_SIGNATURE"
      via: "Environment passthrough from systemd manager"
      pattern: "PassEnvironment|Environment"
---

<objective>
Fix Pypr daemon failing to connect to Hyprland after boot and ensure resilient operation.

Purpose: Pypr provides zoom (SUPER+Z) and scratchpads (blueman) functionality. Currently it fails on every
boot with "No supported environment detected" because: (1) the service starts via default.target before
Hyprland is running, (2) pypr exits with code 0 on error so Restart=on-failure never triggers, and
(3) the launch.conf delayed start is a no-op because systemd sees the service as already activated
with Result=success.

Output: Working pypr service that starts reliably after Hyprland and auto-recovers from failures.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@linuxmini/systemd/user/pypr.service
@linuxmini/config/hypr/launch.conf
@linuxmini/config/pypr/config.toml
@linuxmini/config/hypr/keybinds.conf
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix pypr.service for Hyprland environment and resilient restarts</name>
  <files>linuxmini/systemd/user/pypr.service</files>
  <action>
Update the pypr systemd service unit at `linuxmini/systemd/user/pypr.service` with these changes:

[Unit] section:
- Keep `Description`, `PartOf=graphical-session.target`, `After=graphical-session.target`
- Add `ConditionEnvironment=HYPRLAND_INSTANCE_SIGNATURE` so the service won't even attempt
  to start if the Hyprland environment variable is not set in the systemd manager. This
  prevents the failed startup before Hyprland runs.

[Service] section:
- Add `PassEnvironment=HYPRLAND_INSTANCE_SIGNATURE` to pass the Hyprland socket identifier
  (matching the pattern used by hypridle.service which works correctly)
- Change `Restart=on-failure` to `Restart=always` because pypr exits with code 0 even on
  RuntimeError, so on-failure never triggers. Restart=always ensures recovery regardless
  of exit code.
- Keep `RestartSec=3` (reasonable backoff)
- Add `StartLimitIntervalSec=300` and `StartLimitBurst=10` to allow 10 restarts in 5 minutes
  before giving up (matching the pattern established in Phase 01-02 for other services)

[Install] section:
- Change `WantedBy=default.target` to `WantedBy=graphical-session.target` so the service
  is only started when a graphical session is active, not at bare login
  </action>
  <verify>
Verify the service file syntax:
- Run: `cd ~/.dotfiles && python setup.py` to apply symlinks
- Run: `systemd-analyze verify --user pypr.service 2>&1` to check for syntax errors
- Run: `systemctl --user cat pypr.service` to confirm the deployed content matches
- Confirm the file contains: Restart=always, PassEnvironment=HYPRLAND_INSTANCE_SIGNATURE,
  ConditionEnvironment=HYPRLAND_INSTANCE_SIGNATURE, WantedBy=graphical-session.target,
  StartLimitIntervalSec=300, StartLimitBurst=10
  </verify>
  <done>
pypr.service has correct dependencies, environment passthrough, and restart behavior.
ConditionEnvironment prevents startup before Hyprland. Restart=always handles pypr's
zero-exit-code crash behavior. WantedBy=graphical-session.target prevents premature activation.
  </done>
</task>

<task type="auto">
  <name>Task 2: Fix launch.conf to use restart instead of start for pypr</name>
  <files>linuxmini/config/hypr/launch.conf</files>
  <action>
In `linuxmini/config/hypr/launch.conf`, on line 30 where pypr.service is started alongside
other services with `sleep 5 && systemctl --user start`:

Change `start` to `restart` for pypr.service ONLY. The reason: if pypr was previously started
by systemd (from WantedBy) and exited successfully (Result=success), `systemctl start` is a
no-op because systemd considers it already activated. Using `restart` forces a fresh start
with the now-available Hyprland environment variables.

The other services on that line (waybar, hypridle, clipse, jellyfin-mpv-shim) should keep using
`start` since they work correctly. Split pypr out of that line to use restart separately.

Change line 30 from:
```
exec-once = sleep 5 && systemctl --user start waybar.service hypridle.service pypr.service clipse.service jellyfin-mpv-shim.service
```
To:
```
exec-once = sleep 5 && systemctl --user start waybar.service hypridle.service clipse.service jellyfin-mpv-shim.service
exec-once = sleep 5 && systemctl --user restart pypr.service
```

This ensures pypr gets a clean start with the correct environment every time Hyprland launches,
even if the service was previously activated and failed.
  </action>
  <verify>
- Run: `cd ~/.dotfiles && python setup.py` to apply symlinks
- Confirm launch.conf has separate pypr restart line
- Confirm the other services still have their `start` line intact
- Test by running: `systemctl --user restart pypr.service` and verify pypr starts:
  `systemctl --user status pypr.service` should show Active: active (running)
- Test zoom works: `pypr zoom ++0.5` should respond without error
  </verify>
  <done>
Pypr restarts cleanly via launch.conf after Hyprland initializes. The restart command
ensures a fresh activation regardless of prior service state. Pypr zoom and scratchpad
functionality works. The service will also self-recover from crashes via Restart=always.
  </done>
</task>

</tasks>

<verification>
1. `systemctl --user status pypr.service` shows Active: active (running)
2. `pypr zoom ++0.5` works (tests socket connectivity)
3. `pypr zoom` resets zoom (confirms bidirectional communication)
4. Service file has all required directives: grep for Restart=always, PassEnvironment,
   ConditionEnvironment, WantedBy=graphical-session.target, StartLimitIntervalSec
5. launch.conf has `restart pypr.service` on a separate line from other services
</verification>

<success_criteria>
- Pypr service starts and stays running after manual restart
- Zoom keybind (SUPER+Z) works
- Service configured to survive reboots with proper Hyprland dependency chain
- Restart=always handles pypr's zero-exit-code crash behavior
- StartLimitBurst/Interval provides crash loop protection
</success_criteria>

<output>
After completion, create `.planning/quick/8-fix-pypr-daemon-connectivity-in-hyprland/8-SUMMARY.md`
</output>
