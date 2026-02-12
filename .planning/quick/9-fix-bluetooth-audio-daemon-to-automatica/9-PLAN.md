---
phase: quick-9
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - linuxmini/scripts/hyprland/bluetooth_audio_manager.py
autonomous: false
must_haves:
  truths:
    - "When WH-1000XM3 connects, default audio sink switches to it automatically"
    - "When WH-1000XM3 disconnects, default audio sink falls back to next priority device"
    - "Priority order is honored: WH-1000XM3 > Google Home Speaker"
  artifacts:
    - path: "linuxmini/scripts/hyprland/bluetooth_audio_manager.py"
      provides: "Bluetooth connection management + automatic audio sink switching"
      contains: "wpctl"
  key_links:
    - from: "bluetooth_audio_manager.py reconcile()"
      to: "wpctl set-default"
      via: "subprocess call after successful connection"
      pattern: "wpctl.*set-default"
---

<objective>
Add automatic PipeWire/WirePlumber default sink switching to the bluetooth audio manager daemon.

Purpose: The daemon currently manages Bluetooth connections with priority logic, but audio output stays on whichever device was previously set as default. When the WH-1000XM3 headphones connect, audio should automatically route to them.

Output: Updated bluetooth_audio_manager.py that switches the default audio sink after device connection changes.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@linuxmini/scripts/hyprland/bluetooth_audio_manager.py
@linuxmini/systemd/user/bluetooth-audio-manager.service
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add PipeWire sink switching to bluetooth audio manager</name>
  <files>linuxmini/scripts/hyprland/bluetooth_audio_manager.py</files>
  <action>
Modify the existing bluetooth_audio_manager.py to switch the default audio sink after reconciliation changes the connected device. The system uses PipeWire with WirePlumber, so use `wpctl` for sink management.

Add a `set_default_sink(device_name, mac)` function that:
1. Runs `wpctl status` and parses the Audio > Sinks section to find a sink matching the device name or MAC address (Bluetooth sinks typically contain the device name or a bluez identifier like `bluez_output.XX_XX_XX_XX_XX_XX`)
2. Extracts the WirePlumber node ID for the matching sink
3. Runs `wpctl set-default {node_id}` to set it as default
4. Logs the sink switch and sends a notification

Important implementation details:
- Bluetooth audio sinks take a few seconds to appear in PipeWire after a device connects. Add a retry mechanism: after a successful Bluetooth connection, try to find and set the sink up to 5 times with 2-second delays between attempts.
- Parse `wpctl status` output carefully. The Sinks section looks like:
  ```
   Audio
   ├─ Devices:
   │  ...
   ├─ Sinks:
   │      47. device_name [vol: 0.50]
   │   *  52. other_device [vol: 0.75]
   ```
  The `*` indicates current default. The number before the `.` is the node ID.
- Match sinks by checking if the device name (e.g., "WH-1000XM3") appears in the sink name, case-insensitive. Also try matching by MAC with underscores (e.g., "38_18_4C_AE_2B_E3") since bluez sinks often use that format.
- If no matching sink is found after retries, log a warning but don't fail.

Integrate sink switching into the reconcile() function:
- After a successful `connect_with_retries()` call, call `set_default_sink()` for the newly connected device
- When the highest-priority device is already connected (the "nothing to do" path), ALSO call `set_default_sink()` to ensure the default sink is correct (handles the case where sink was manually changed)
- When a device disconnects and a lower-priority device is still connected, set the sink to the lower-priority device

Also add sink switching to the `periodic_reconcile` path so that every 30 seconds, the default sink is verified to match the highest-priority connected device.

Do NOT remove the existing disconnect-lower-priority logic. The "only one connection at a time" behavior should remain since the Google Home Speaker and WH-1000XM3 cannot usefully be connected simultaneously (audio should go to only one).
  </action>
  <verify>
Run `python3 -c "import ast; ast.parse(open('/home/rash/.dotfiles/linuxmini/scripts/hyprland/bluetooth_audio_manager.py').read()); print('Syntax OK')"` to verify no syntax errors.

Manually review the file to confirm:
- `set_default_sink` function exists and uses `wpctl status` + `wpctl set-default`
- `reconcile()` calls `set_default_sink()` after successful connections
- Retry logic exists for sink discovery (sinks take time to appear after BT connect)
- Existing connection management logic is preserved
  </verify>
  <done>
bluetooth_audio_manager.py contains sink switching via wpctl that activates after device connection changes. The daemon will automatically set the default audio output to the highest-priority connected Bluetooth device.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 2: Verify sink switching on real hardware</name>
  <files>linuxmini/scripts/hyprland/bluetooth_audio_manager.py</files>
  <action>
Deploy and verify the updated daemon on linuxmini with real Bluetooth devices.
  </action>
  <verify>
1. Deploy: `cd ~/.dotfiles && python setup.py`
2. Restart daemon: `systemctl --user restart bluetooth-audio-manager`
3. Check logs: `journalctl --user -u bluetooth-audio-manager -f`
4. Test: Connect WH-1000XM3 headphones and verify:
   - Logs show sink discovery and `wpctl set-default` being called
   - Audio output actually switches to headphones (play something)
   - `wpctl status` shows the headphones sink marked with `*`
5. Test disconnect: Turn off headphones, verify audio falls back to Google Home Speaker
  </verify>
  <done>Audio automatically routes to highest-priority connected Bluetooth device without manual intervention.</done>
</task>

</tasks>

<verification>
- Python syntax check passes
- `wpctl` calls are present in the code with proper subprocess handling
- Retry logic handles the delay between BT connect and sink availability
- Existing priority-based connection management is unchanged
</verification>

<success_criteria>
When the WH-1000XM3 headphones connect (either automatically via the daemon or manually), the default audio sink switches to the headphones within ~10 seconds. When they disconnect, audio falls back to the next available priority device.
</success_criteria>

<output>
After completion, create `.planning/quick/9-fix-bluetooth-audio-daemon-to-automatica/9-SUMMARY.md`
</output>
