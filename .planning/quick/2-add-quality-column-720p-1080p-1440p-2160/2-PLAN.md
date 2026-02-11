---
phase: quick-2
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - linuxmini/local/bin/down_d_impl.py
autonomous: true

must_haves:
  truths:
    - "Quality column shows '720p', '1080p', '1440p', or '2160p' when -q flag used"
    - "Quality column shows 'best' when no -q flag given"
    - "Quality column is positioned immediately right of the URL column"
    - "Status column shows only the icon character, no text"
    - "All columns fit within a standard terminal width without wrapping"
  artifacts:
    - path: "linuxmini/local/bin/down_d_impl.py"
      provides: "Quality column and optimized column widths in create_progress_table"
      contains: "Quality"
  key_links:
    - from: "create_progress_table"
      to: "DownloadTask.quality"
      via: "format quality string for display"
      pattern: "task\\.quality"
---

<objective>
Add a Quality column to the down_d progress table and optimize all column widths for a compact display.

Purpose: Let the user see at a glance what video quality is being downloaded (requested or best available).
Output: Updated down_d_impl.py with quality column and tighter column sizing.
</objective>

<execution_context>
@/home/rash/.claude/get-shit-done/workflows/execute-plan.md
@/home/rash/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@linuxmini/local/bin/down_d_impl.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add quality column and optimize column widths in progress table</name>
  <files>linuxmini/local/bin/down_d_impl.py</files>
  <action>
Modify `create_progress_table` in `down_d_impl.py` to add a Quality column and optimize all column widths:

**1. Add Quality column (right of URL):**
- Add column "Quality" right after the URL column, styled "bold white", with `min_width=5`, `justify="center"`
- Format the quality display value from `task.quality`:
  - If quality is a number string ("720", "1080", "1440", "2160"): display as "{quality}p" (e.g. "1080p")
  - If quality is "bestvideo+bestaudio/best" or any other string: display as "best"
- Add the quality value to each `table.add_row()` call as the second positional argument (after URL)

**2. Status column - icon only, centered:**
- Change status strings to icon-only (remove text labels):
  - success: `"[green]✅[/green]"` (was `"[green]✅ Complete[/green]"`)
  - failed: `"[red]❌[/red]"` (was `"[red]❌ Failed[/red]"`)
  - downloading: `"[yellow]⏬[/yellow]"` (was `"[yellow]⏬ Downloading[/yellow]"`)
  - pending: `"[dim]⏳[/dim]"` (was `"[dim]⏳ Pending[/dim]"`)
- Update Status column definition: set `justify="center"`, `min_width=2`, remove ratio, set `width=4`

**3. Progress column - optimize number format:**
- When formatting progress percentage (the fallback when size is unavailable):
  - If `task.progress_pct >= 100`: show as `f"{int(task.progress_pct)}%"` (no decimals)
  - Else: show as `f"{task.progress_pct:.1f}%"` (one decimal)
- Apply the same rule inside `compute_downloaded_size`: when it falls back to percentage display, use int format if >= 100
- Reduce progress bar width from 20 to 15 characters (`bar_width = 15`)

**4. ETA column - tight width:**
- Set ETA column: `min_width=7` (fits "0:00:00" exactly), remove ratio

**5. Speed column - tight width:**
- Set Speed column: `min_width=10` (fits "00.00XiB/s"), remove ratio

**6. URL column - slightly reduced:**
- Keep URL column with `ratio=3`, set `no_wrap=True` (was False)
- Reduce URL truncation from 40 chars to 35: `url_short = task.url[:32] + "..." if len(task.url) > 35 else task.url`

**Column order in table: URL, Quality, Status, Progress, Speed, ETA**
  </action>
  <verify>
Run `python3 -c "import sys; sys.path.insert(0, 'linuxmini/local/bin'); from down_d_impl import create_progress_table, DownloadTask; t = DownloadTask('https://example.com/video', 1, '1080'); t.status = 'downloading'; t.progress_pct = 45.2; t.speed = '1.20MiB/s'; t.eta = '3:24'; t.size = '500.00MiB'; table = create_progress_table({'t1': t}, 1); from rich.console import Console; Console().print(table)"` from the repo root. Verify:
- Quality column shows "1080p"
- Status shows icon only (no text)
- Bar is 15 chars wide
- All columns fit on one line

Also test with "best" quality:
`python3 -c "import sys; sys.path.insert(0, 'linuxmini/local/bin'); from down_d_impl import create_progress_table, DownloadTask; t = DownloadTask('https://example.com/video', 1, 'bestvideo+bestaudio/best'); t.status = 'success'; t.progress_pct = 100; t.size = '1.23GiB'; table = create_progress_table({'t1': t}, 1); from rich.console import Console; Console().print(table)"` - Quality column shows "best", progress shows integer 100 (no decimals).
  </verify>
  <done>
- Quality column appears right of URL showing "720p"/"1080p"/"1440p"/"2160p" or "best"
- Status column is icon-only, centered
- Progress uses int format at 100%, 1 decimal below
- Progress bar is 15 chars wide
- All columns fit within terminal width
  </done>
</task>

<task type="auto">
  <name>Task 2: Deploy changes via setup.py</name>
  <files>linuxmini/local/bin/down_d_impl.py</files>
  <action>
Run `cd /home/rash/.dotfiles && python setup.py` to deploy the updated down_d_impl.py to ~/.local/bin/ via symlinks.
  </action>
  <verify>
Verify the symlink is in place: `ls -la ~/.local/bin/down_d_impl.py` should show a symlink pointing to the dotfiles source.
  </verify>
  <done>Updated down_d_impl.py is deployed and ready for use.</done>
</task>

</tasks>

<verification>
- `python3 ~/.local/bin/down_d_impl.py --help` runs without error
- Quality column renders correctly for both explicit quality and "best" default
- Table fits in standard 80-column terminal (verify visually from test output)
</verification>

<success_criteria>
- Quality column visible in progress table showing requested quality or "best"
- All column widths optimized: status icon-only, progress bar 15 chars, tight ETA/speed
- No visual wrapping or overflow in normal terminal widths
</success_criteria>

<output>
After completion, create `.planning/quick/2-add-quality-column-720p-1080p-1440p-2160/2-SUMMARY.md`
</output>
