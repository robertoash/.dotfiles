---
phase: quick-1
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - linuxmini/local/bin/down_d_impl.py
autonomous: true
must_haves:
  truths:
    - "Progress bar shows human-readable downloaded/total sizes instead of percentage"
    - "Completed downloads show total file size instead of 100%"
    - "Bar still visually conveys percentage (filled vs unfilled blocks remain)"
  artifacts:
    - path: "linuxmini/local/bin/down_d_impl.py"
      provides: "Updated progress display with human-readable sizes"
      contains: "format_size"
  key_links:
    - from: "parse_progress_line"
      to: "create_progress_table"
      via: "task.size and task.progress_pct used to compute downloaded amount"
      pattern: "task\\.progress_pct.*task\\.size"
---

<objective>
Update the down_d progress display to show human-readable downloaded/total sizes (e.g., "112.5MiB/430.7MiB") instead of percentage numbers next to the progress bar.

Purpose: The progress bar already visually conveys percentage. Showing actual sizes is more informative -- the user can see how much data has been transferred and the total file size at a glance.
Output: Modified `down_d_impl.py` with size-based progress display.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@linuxmini/local/bin/down_d_impl.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Replace percentage display with human-readable size display in progress table</name>
  <files>linuxmini/local/bin/down_d_impl.py</files>
  <action>
Modify `create_progress_table()` in `down_d_impl.py` to show downloaded/total sizes instead of percentage next to the bar.

**Current behavior (line 230):**
```python
progress = f"[yellow]{bar}[/yellow] {task.progress_pct:.1f}%"
```

**Target behavior:**
```python
progress = f"[yellow]{bar}[/yellow] {downloaded_str}/{task.size}"
```

Specific changes:

1. Add a helper function `compute_downloaded_size(pct: float, total_size_str: str) -> str` that:
   - Parses the total size string from yt-dlp (e.g., "430.74MiB", "1.23GiB", "512.00KiB")
   - Computes downloaded = pct/100 * total_value
   - Returns the downloaded amount in the SAME unit as total (e.g., if total is "430.74MiB", downloaded at 26.7% returns "115.0MiB")
   - Handles edge cases: empty/missing size string returns pct as fallback display

2. In `create_progress_table()`, update the "downloading" status branch (line 225-230):
   - Compute downloaded string using the helper
   - Display: `[yellow]{bar}[/yellow] {downloaded_str}/{task.size}`
   - If task.size is empty (not yet parsed from output), fall back to just showing the percentage: `{bar} {task.progress_pct:.1f}%`

3. Update the "success" status branch (line 220-221):
   - Change from `[green]bar[/green] 100%` to `[green]bar[/green] {task.size}` if size is known
   - Fall back to `[green]bar[/green] Done` if size was never captured

Do NOT change the bar itself (the filled/unfilled block characters) -- it should still be based on percentage. Only the text label next to the bar changes.

Do NOT modify `parse_progress_line()` -- it already correctly extracts the size string (group 2) into `task.size`.
  </action>
  <verify>
Run `python3 -c "import ast; ast.parse(open('linuxmini/local/bin/down_d_impl.py').read()); print('Syntax OK')"` from the dotfiles root to verify no syntax errors.

Manually verify the helper function logic by checking that `compute_downloaded_size(50.0, '430.74MiB')` would yield approximately `215.4MiB`.
  </verify>
  <done>
Progress bar in downloading state shows "bar downloaded/total" (e.g., "115.0MiB/430.7MiB") instead of "bar 26.7%". Completed downloads show "bar total_size" or "bar Done". Bar itself still reflects percentage visually via filled/unfilled blocks.
  </done>
</task>

<task type="auto">
  <name>Task 2: Apply dotfiles changes via setup.py</name>
  <files>linuxmini/local/bin/down_d_impl.py</files>
  <action>
Run `cd /home/rash/.dotfiles && python setup.py` to apply the changed `down_d_impl.py` to its symlinked target location (`~/.local/bin/down_d_impl.py`).

Verify the symlink target reflects the updated code by checking the file contains the new `compute_downloaded_size` function.
  </action>
  <verify>
Run `grep -c 'compute_downloaded_size' ~/.local/bin/down_d_impl.py` -- should return 1 or more (confirming the function exists in the deployed file).
  </verify>
  <done>The updated down_d_impl.py is deployed to ~/.local/bin/ via the dotfiles setup mechanism.</done>
</task>

</tasks>

<verification>
- `python3 -c "import ast; ast.parse(open('/home/rash/.dotfiles/linuxmini/local/bin/down_d_impl.py').read())"` exits 0
- `grep 'compute_downloaded_size' /home/rash/.dotfiles/linuxmini/local/bin/down_d_impl.py` finds the helper function
- Progress column no longer contains `:.1f}%` pattern for the downloading state (percentage removed from bar label)
- Progress column for downloading state contains `/{task.size}` pattern (shows total size)
</verification>

<success_criteria>
The down_d progress display shows human-readable downloaded/total file sizes next to the progress bar instead of a percentage number. The bar still visually conveys progress via filled/unfilled blocks.
</success_criteria>

<output>
After completion, create `.planning/quick/1-display-memory-usage-in-human-readable-f/1-SUMMARY.md`
</output>
