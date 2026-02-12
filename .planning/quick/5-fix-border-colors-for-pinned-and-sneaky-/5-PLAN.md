---
phase: quick-5
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - linuxmini/config/hypr/windowrules.conf
autonomous: true
must_haves:
  truths:
    - "Pinned windows show yellow border when focused and red border when unfocused"
    - "Sneaky-tagged windows show yellow border when focused and purple border when unfocused"
    - "Border colors change correctly on focus/unfocus state transitions"
  artifacts:
    - path: "linuxmini/config/hypr/windowrules.conf"
      provides: "Corrected border_color rules for pinned and sneaky windows"
      contains: "border_color rgb"
  key_links:
    - from: "linuxmini/config/hypr/windowrules.conf"
      to: "Hyprland window manager"
      via: "windowrule border_color directive"
      pattern: "border_color rgb\\("
---

<objective>
Fix border colors for pinned and sneaky windows so they display correct solid colors on focus/unfocus state changes.

Purpose: The current `border_color` windowrules have an invalid `1` prefix parameter that Hyprland's parser does not recognize as an override flag. This causes the border colors to not apply correctly. The `1` is being parsed as a color value, breaking the active/inactive color assignment.

Output: Corrected windowrules.conf with proper `border_color <active> <inactive>` syntax.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@linuxmini/config/hypr/windowrules.conf
@linuxmini/config/hypr/hyprland.conf
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix border_color syntax for pinned and sneaky window rules</name>
  <files>linuxmini/config/hypr/windowrules.conf</files>
  <action>
Fix the two broken `border_color` windowrules that have an invalid `1` prefix parameter.

Hyprland's border_color syntax is: `border_color <active_color> <inactive_color>` (for solid colors).
The `1` in the current rules is NOT a valid override flag -- it gets parsed as a color value, breaking the intended active/inactive color mapping.

**Line 30** (pinned windows):
- Current:  `windowrule = border_color 1 rgb(ffff00) rgb(ff0000), match:pin 1`
- Fix to:   `windowrule = border_color rgb(ffff00) rgb(ff0000), match:pin 1`
- Meaning: Yellow (#ffff00) when focused/active, Red (#ff0000) when unfocused/inactive

**Line 34** (sneaky windows):
- Current:  `windowrule = border_color 1 rgb(ffff00) rgb(d5a6ff), match:tag sneaky`
- Fix to:   `windowrule = border_color rgb(ffff00) rgb(d5a6ff), match:tag sneaky`
- Meaning: Yellow (#ffff00) when focused/active, Purple (#d5a6ff) when unfocused/inactive

Also update the comment block on lines 27-29. The old comment references a Hyprland gradient bug and a TODO about using gradient syntax in the future. Replace it with a concise comment explaining the current solid-color choice:
- Replace the 3-line block (lines 27-29) with a single comment: `# Pinned windows: yellow (focused) / red (unfocused)`

Do NOT change any other rules in the file. The `match:pin 1` at the end of line 30 is correct (it matches pinned windows) -- only the `1` immediately after `border_color` is the problem.
  </action>
  <verify>
Run `cd ~/.dotfiles && python setup.py` to apply the symlinks.
Then run `hyprctl reload` to reload Hyprland config.
Verify no errors in `hyprctl systeminfo` or `journalctl --user -u hyprland -n 20 --no-pager` related to windowrule parsing.
Grep the file to confirm no remaining `border_color 1` patterns: `grep 'border_color 1' linuxmini/config/hypr/windowrules.conf` should return empty.
  </verify>
  <done>
The two border_color rules no longer have the invalid "1" prefix. Pinned windows will show yellow/red borders on focus/unfocus. Sneaky windows will show yellow/purple borders on focus/unfocus.
  </done>
</task>

</tasks>

<verification>
- `grep 'border_color' linuxmini/config/hypr/windowrules.conf` shows only valid `border_color rgb(...)` syntax (no leading `1`)
- `hyprctl reload` completes without errors
- Pin a window and verify: focused = yellow border, unfocused = red border
- Tag a window as sneaky and verify: focused = yellow border, unfocused = purple border
</verification>

<success_criteria>
- No `border_color 1` patterns remain in windowrules.conf
- Hyprland config reloads cleanly
- Pinned window borders: yellow (active) / red (inactive)
- Sneaky window borders: yellow (active) / purple (inactive)
</success_criteria>

<output>
After completion, create `.planning/quick/5-fix-border-colors-for-pinned-and-sneaky-/5-SUMMARY.md`
</output>
