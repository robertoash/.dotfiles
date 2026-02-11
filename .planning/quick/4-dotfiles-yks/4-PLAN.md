---
phase: quick-4
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - common/config/fish/functions/__dot_expand_widget.fish
autonomous: true
must_haves:
  truths:
    - "Typing ... still expands to grandparent directory path"
    - "Each additional . goes up one more level and updates fzf listing"
    - "Selecting a directory from fzf inserts it on the command line"
    - "Pressing Esc/Ctrl+C in fzf keeps the current path"
    - "Dot expansion feels instant with no perceptible lag"
    - "Normal single-dot typing is unaffected"
  artifacts:
    - path: "common/config/fish/functions/__dot_expand_widget.fish"
      provides: "Optimized dot expansion widget"
      contains: "__dot_expand_widget"
  key_links:
    - from: "common/config/fish/conf.d/06_keybindings.fish"
      to: "common/config/fish/functions/__dot_expand_widget.fish"
      via: "bind -M insert . __dot_expand_widget"
      pattern: "bind.*__dot_expand_widget"
---

<objective>
Fix laggy dot expansion in fish shell by replacing heavyweight fd+fzf recursive relaunch pattern with fast native globbing and fzf's built-in reload mechanism.

Purpose: The current __dot_expand_widget uses `fd -Hi --no-ignore-vcs` (a recursive file finder) for what is a single-depth directory listing, and relaunches fzf from scratch on each additional dot press. This causes perceptible lag. Native shell globbing is orders of magnitude faster for listing immediate child directories, and fzf's `reload()` action can update the listing in-place without teardown/restart.

Output: Rewritten __dot_expand_widget.fish with same user-facing behavior but dramatically reduced latency.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@common/config/fish/functions/__dot_expand_widget.fish
@common/config/fish/conf.d/06_keybindings.fish
</context>

<tasks>

<task type="auto">
  <name>Task 1: Replace fd with native globbing for directory listing</name>
  <files>common/config/fish/functions/__dot_expand_widget.fish</files>
  <action>
Rewrite __dot_expand_widget.fish with these specific optimizations:

1. **Replace `fd` with native globbing in __dot_expand_fzf helper:**
   - Current: `fd -Hi --no-ignore-vcs -t d --max-depth 1 . "$search_dir" 2>/dev/null`
   - Replace with: `command ls -1dp "$search_dir"/*/ 2>/dev/null | string replace -r '/$' ''`
   - This lists immediate subdirectories using the kernel's readdir() instead of spawning fd, which does unnecessary stat() calls and inode traversal for a depth-1 listing.
   - If hidden directories are desired (the original used `-Hi`), use `command ls -1Adp "$search_dir"/*/ "$search_dir"/.*/ 2>/dev/null | string match -v '*/.\$' | string match -v '*/\.\.\$' | string replace -r '/$' ''` to include dotdirs while excluding . and ..

2. **Replace recursive fzf relaunch with fzf's `reload()` action:**
   - Current approach: fzf `--bind ".:execute-silent(touch $marker)+abort"` kills fzf, fish detects marker file, computes parent, relaunches fzf. Each cycle = fzf teardown + fd spawn + fd scan + fzf startup.
   - New approach: Use a single fzf invocation with `--bind` that handles the `.` key:
     - Create a small helper script (inline or /tmp) that takes current search_dir, computes parent via dirname, lists its children, and outputs them.
     - Use fzf's `--bind ".:reload(...)` + `--bind ".:change-header(...)"` to update the directory listing in-place.
     - Track the "current level" by writing the current search path to a temp file that the reload script reads.
     - Specifically: `set -l state_file /tmp/dot-expand-state-$fish_pid` and write the initial search_dir to it. The reload command reads the state file, goes up one level with dirname, writes the new path back, and lists that directory's children.
   - The fzf bind should look like:
     ```
     --bind ".:reload(bash -c 'dir=\$(cat {state_file}); parent=\$(dirname \"\$dir\"); if [ \"\$parent\" != \"\$dir\" ]; then echo \"\$parent\" > {state_file}; ls -1dp \"\$parent\"/*/ 2>/dev/null | sed \"s|/\$||\"; else ls -1dp \"\$dir\"/*/ 2>/dev/null | sed \"s|/\$||\"; fi')+change-header(..going up..)"
     ```
   - After fzf exits, read the state file to get the final directory level, clean up the state file.

3. **Remove marker file IPC:**
   - Delete all code related to `/tmp/dot-expand-marker-$fish_pid` (creation, touch, test, rm).
   - The state file for tracking current directory replaces it.

4. **Update the commandline token after fzf exits:**
   - If fzf returns a selected result: insert it as the token (same as current).
   - If fzf exits with no selection (abort/esc): read the state file to get the final ancestor path and insert that as the token (so the user keeps whatever level they navigated to).
   - Clean up: `command rm -f $state_file`

5. **Keep __dot_expand_widget main function logic identical:**
   - Case 1 (token is ".."): Still computes grandparent, replaces token, launches fzf.
   - Case 2 (token is expanded path with __dot_expand_level set): Still goes up one level, replaces token, launches fzf.
   - Case 3 (normal dot): Still just inserts '.'.
   - The change is ONLY in __dot_expand_fzf (the helper).

6. **Preserve the display format:** fzf should show full paths (same as current behavior) so the user can see where they are.
  </action>
  <verify>
  Verification steps (manual, since this is an interactive shell widget):
  1. Open a new fish shell
  2. Type `cd ...` - should expand to grandparent path and show fzf with directories at that level
  3. Press `.` inside fzf - listing should update in-place to show directories one level higher (no fzf flicker/restart)
  4. Select a directory - should insert it on the command line
  5. Press Esc in fzf - should keep the ancestor path on the command line
  6. Type a single `.` in normal context - should just insert a dot
  7. Confirm there is no perceptible lag on any of these operations
  </verify>
  <done>
  Dot expansion widget works identically to before from the user's perspective but with no perceptible lag. Directory listing uses native globbing instead of fd. Additional dot presses update fzf in-place via reload instead of recursive relaunch.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 2: Verify dot expansion feels responsive</name>
  <what-built>Optimized dot expansion widget with native globbing and in-place fzf reload</what-built>
  <how-to-verify>
    1. Open a new fish shell (or run `source ~/.config/fish/functions/__dot_expand_widget.fish` to reload)
    2. Navigate to a directory with several subdirectories (e.g., ~ or /home)
    3. Type `cd ...` and observe:
       - Should expand to grandparent path instantly
       - fzf should appear with directory listing
    4. Press `.` inside fzf:
       - Listing should update in-place (no flicker or restart)
       - Header or prompt should indicate you went up a level
    5. Select a directory with Enter - should be inserted on command line
    6. Repeat but press Esc - should keep the ancestor path
    7. In a fresh prompt, type `echo hello.world` - single dots should work normally
    8. Compare responsiveness to before - should feel noticeably snappier, especially the additional-dot navigation
  </how-to-verify>
  <resume-signal>Type "approved" or describe any issues</resume-signal>
</task>

</tasks>

<verification>
- `source ~/.config/fish/functions/__dot_expand_widget.fish` loads without errors
- `cd ...` triggers expansion and fzf picker
- Additional dots in fzf update listing in-place
- No `fd` process spawned during dot expansion (verify with `ps aux | grep fd` in another terminal)
- Normal dot insertion unaffected
</verification>

<success_criteria>
- Dot expansion has no perceptible lag on any keypress
- fzf listing updates in-place when pressing additional dots (no relaunch flicker)
- All existing dot expansion behavior preserved (grandparent expansion, directory selection, cancel behavior)
- No fd dependency for the dot expansion widget
</success_criteria>

<output>
After completion, create `.planning/quick/4-dotfiles-yks/4-SUMMARY.md`
</output>
