---
phase: quick-3
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - linuxmini/local/bin/down_d_impl.py
autonomous: true
must_haves:
  truths:
    - "Quality column shows the actual resolution being downloaded (e.g., 1080p, 720p), not the requested quality argument"
    - "When quality=best is used, the actual resolved resolution is displayed instead of 'best'"
    - "Quality updates dynamically during download as the resolution info becomes available"
  artifacts:
    - path: "linuxmini/local/bin/down_d_impl.py"
      provides: "Resolution parsing from yt-dlp output"
      contains: "print-to-file.*height"
  key_links:
    - from: "build_tier_command"
      to: "DownloadTask.quality"
      via: "--print-to-file writes height to temp file, download_with_progress reads it"
      pattern: "print-to-file.*height"
---

<objective>
Parse the actual video resolution from yt-dlp during download instead of displaying the requested quality argument or "best".

Purpose: Currently the Quality column shows whatever the user passed (e.g., "1080" -> "1080p") or "best" as fallback. When users request "best" or when yt-dlp falls back to a different resolution than requested, the displayed quality is misleading. We need to show what's actually being downloaded.

Output: Updated down_d_impl.py that extracts real resolution via yt-dlp's --print-to-file and displays it in the progress table.
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
  <name>Task 1: Add --print-to-file to yt-dlp commands and parse actual resolution</name>
  <files>linuxmini/local/bin/down_d_impl.py</files>
  <action>
Three changes to down_d_impl.py:

1. **Modify `build_tier_command` to accept a `height_file` parameter and add `--print-to-file` flag:**
   - Add `height_file: str` parameter to `build_tier_command(url, tier, quality, height_file)`
   - Add `"--print-to-file", "%(height)s", height_file` to the `base_cmd` list right after `--add-metadata`
   - This tells yt-dlp to write the actual resolved video height (e.g., "1080") to the specified file during download
   - This works with all tiers including external downloaders (axel) because yt-dlp resolves formats before handing off

2. **Modify `download_with_progress` to read the height file and update task.quality:**
   - After `task.status = "downloading"`, define a `height_file` path: `tmpdir / f"{task_id}_height.txt"`
   - Pass `height_file` (as string) to `build_tier_command` when constructing the command
   - Wait, actually `download_with_progress` receives `cmd` pre-built. So instead:
   - Change approach: have `download_with_progress` accept `height_file: Path` as parameter
   - In the `download_tier` function, construct the height_file path and pass it to both `build_tier_command` and `download_with_progress`
   - In the output reading loop inside `download_with_progress`, after parsing each line, check if `height_file.exists()` and `task.quality` hasn't been updated yet (use a flag like checking if quality is still the original requested value)
   - When height_file exists, read it: `height_file.read_text().strip()`. If it's a valid number (e.g., "1080", "720", "1440", "2160", "480", "360"), set `task.quality = height_value` (just the number string)
   - Only read the file once (set a local bool `height_resolved = False`, flip to True after reading)

3. **Update `create_progress_table` quality display logic:**
   - The current logic checks `if task.quality in ("720", "1080", "1440", "2160")` and formats as `{quality}p`, else shows "best"
   - Change to: if `task.quality` is a numeric string (use `task.quality.isdigit()`), display as `{task.quality}p`
   - This handles any resolution (480p, 720p, 1080p, 1440p, 2160p, etc.) not just the 4 hardcoded values
   - For non-numeric values (before resolution is known, or audio-only), display "..." while downloading or "best" if still pending

4. **Update `download_tier` function's `download_wrapper`:**
   - Construct `height_file = tmpdir_path / f"{task_id}_height.txt"`
   - Pass `height_file` (as string) to `build_tier_command(url, tier, quality, str(height_file))`
   - Pass `height_file` (as Path) to `download_with_progress(task, cmd, tmpdir_path, task_id, height_file)`
   - Update the `download_wrapper` inner function signature and the call to `build_tier_command` accordingly

Implementation detail: The `--print-to-file` flag writes the value BEFORE download begins (during format resolution), so the height file will be available very early in the download process. The progress loop will pick it up on the next iteration.
  </action>
  <verify>
  - `python -c "import ast; ast.parse(open('linuxmini/local/bin/down_d_impl.py').read())"` -- confirms valid Python syntax
  - Grep for `print-to-file` in the file to confirm the flag is added
  - Grep for `height_file` to confirm the reading logic exists
  - Grep for `isdigit` to confirm the display logic handles arbitrary resolutions
  - Review that `build_tier_command` signature includes `height_file` parameter
  - Review that `download_with_progress` reads the height file in the output loop
  </verify>
  <done>
  - build_tier_command adds --print-to-file %(height)s to all tier commands
  - download_with_progress reads the height file and updates task.quality with actual resolution
  - create_progress_table displays any numeric resolution as Np (e.g., 1080p, 720p) and "..." while resolving
  - Quality column reflects actual downloaded resolution, not requested quality argument
  </done>
</task>

</tasks>

<verification>
- File parses as valid Python (ast.parse)
- --print-to-file flag present in build_tier_command
- height_file reading logic in download_with_progress
- Quality display handles arbitrary numeric resolutions
- No regressions: progress parsing, size display, status indicators all unchanged
</verification>

<success_criteria>
- When downloading with -q 1080, if yt-dlp resolves to 1080p, shows "1080p" (same as before but now verified)
- When downloading with -q 1080 but only 720p available, shows "720p" (the actual resolution, not "1080p")
- When downloading without -q (best), shows actual resolution like "1080p" instead of "best"
- Quality updates early in download (during format resolution phase, before significant progress)
</success_criteria>

<output>
After completion, create `.planning/quick/3-parse-actual-video-quality-from-yt-dlp-o/3-SUMMARY.md`
</output>
