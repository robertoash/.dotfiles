---
phase: quick-11
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - common/config/fish/conf.d/startup_functions/smart_dir_zjump.fish
autonomous: true
must_haves:
  truths:
    - "Bare `cd` (no args) opens fzf picker showing Last dir at top in yellow, then zoxide dirs below"
    - "Selecting a dir in fzf immediately cd's into it"
    - "Pressing Escape or Ctrl-C in fzf cancels without changing directory"
    - "`cd <args>` works exactly as today (zoxide query via __zoxide_z)"
    - "The ping-pong `z` behavior (bare cd alternating between two dirs) is replaced by the fzf picker"
  artifacts:
    - path: "common/config/fish/conf.d/startup_functions/smart_dir_zjump.fish"
      provides: "Updated z function with fzf picker on bare cd"
  key_links:
    - from: "z function (bare cd)"
      to: "fzf"
      via: "piped zoxide query -l with __last_working_dir prepended"
      pattern: "fzf.*--header\\|--ansi"
---

<objective>
Add fuzzy search to bare `cd` (which aliases to `__smart_cd` -> `z`).

When user types `cd` with no arguments, instead of the current ping-pong behavior (jumping to __last_working_dir), open an fzf picker showing:
1. Top line: "Last" entry = `__last_working_dir`, highlighted in yellow (ANSI yellow)
2. Below: zoxide directories in priority order

Selecting any entry immediately cd's into that directory. Cancelling (Esc/Ctrl-C) does nothing.

`cd <args>` remains completely unchanged (passes through to `__zoxide_z`).

Purpose: Faster directory navigation with visual selection instead of blind ping-pong.
Output: Modified `smart_dir_zjump.fish` with fzf-integrated bare cd.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@common/config/fish/conf.d/startup_functions/smart_dir_zjump.fish
@common/config/fish/functions/__smart_cd.fish
@common/config/fish/conf.d/04_fzf.fish
@common/config/fish/conf.d/03_aliases.fish
</context>

<tasks>

<task type="auto">
  <name>Task 1: Replace bare cd ping-pong with fzf directory picker</name>
  <files>common/config/fish/conf.d/startup_functions/smart_dir_zjump.fish</files>
  <action>
Modify the `z` function's no-arguments branch (line 70 onward in smart_dir_zjump.fish). Replace the current ping-pong logic with an fzf picker.

The new bare-cd flow:

1. Build the fzf input list:
   - If `__last_working_dir` is set, non-empty, is a directory, and differs from PWD: prepend it as a yellow-highlighted "Last" entry using ANSI escape codes. Format: `\033[33m__last_working_dir\033[0m` (yellow text). This line should be the FIRST line in the fzf list.
   - Then append all zoxide dirs (`zoxide query -l`), filtering out `$PWD` and `__last_working_dir` (to avoid duplicates).

2. Pipe into fzf with these options:
   - `--ansi` to render the yellow color
   - `--height 40%` `--reverse` for dropdown style (matching existing fzf usage in the codebase)
   - `--no-sort` to preserve zoxide priority ordering
   - `--header 'cd to...'` as a brief header
   - `--color` matching the existing FZF color scheme from 04_fzf.fish: `'fg:#ffffff,fg+:#ffffff,bg:#010111,preview-bg:#010111,border:#7dcfff'`
   - No preview (directories only, keep it fast)

3. On selection:
   - Strip ANSI codes from the selected result (in case user picked the yellow "Last" entry). Use: `string replace -ra '\e\[[0-9;]*m' '' -- "$selected"`
   - If result is non-empty and is a valid directory:
     - Save current `$PWD` as `prev_dir`
     - `builtin cd` into the selected directory
     - Update `__last_working_dir` to `prev_dir`
     - Add `prev_dir` to `__dir_history` with reason "z triggered" (same pattern as existing code)
   - If result is empty (user cancelled): do nothing, return 0

4. Keep the `else` branch (with arguments) completely unchanged - it still calls `__zoxide_z $argv` with the same history tracking.

5. Keep ALL other functions unchanged: `__track_dir_entry`, `zh`, the initialization block at the top.

Important implementation details:
- Use `printf` for ANSI codes, not `echo -e` (fish does not support `echo -e`)
- The fzf input should be built with printf piping, e.g.: `begin; printf '\e[33m%s\e[0m\n' "$__last_working_dir"; zoxide query -l | ...; end | fzf ...`
- Filter PWD and __last_working_dir from zoxide output using `string match -v` or grep
- The ANSI stripping after fzf selection is critical - fzf returns the raw ANSI string for colored entries
  </action>
  <verify>
1. `cd ~/.dotfiles && python setup.py` to deploy the symlink
2. Open a new fish shell
3. Test bare `cd`: should open fzf with yellow "Last" dir at top, zoxide dirs below
4. Test `cd dotfiles`: should work as before (zoxide jump, no fzf)
5. Test cancelling fzf with Escape: should stay in current dir
6. Test `zh`: should still show directory history correctly
  </verify>
  <done>
Bare `cd` opens fzf picker with yellow-highlighted Last dir at top and zoxide dirs below. Selecting a dir cd's into it. Escape cancels cleanly. `cd <args>` unchanged. All existing directory tracking (history, ping-pong updates) preserved.
  </done>
</task>

</tasks>

<verification>
- `fish -n common/config/fish/conf.d/startup_functions/smart_dir_zjump.fish` passes (no syntax errors)
- Bare `cd` shows fzf with Last dir in yellow at top
- `cd <query>` uses zoxide as before
- `zh` shows correct history after using the fzf picker
</verification>

<success_criteria>
- Bare cd opens fzf picker with Last dir highlighted yellow, zoxide dirs below
- Selecting a dir immediately navigates there
- cd with arguments works identically to current behavior
- No regressions in directory history tracking
</success_criteria>

<output>
After completion, create `.planning/quick/11-integrating-fuzzy-search-into-my-cd-func/11-SUMMARY.md`
</output>
