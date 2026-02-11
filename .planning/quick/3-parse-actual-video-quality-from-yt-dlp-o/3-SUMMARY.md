---
phase: quick-3
plan: 01
subsystem: cli
tags: [yt-dlp, video-download, progress-display, resolution-parsing]

requires:
  - phase: quick-2
    provides: Quality column in down_d progress table
provides:
  - Actual video resolution display via yt-dlp --print-to-file
affects: [down_d, video-downloads]

tech-stack:
  added: []
  patterns: [yt-dlp --print-to-file for metadata extraction to temp files]

key-files:
  created: []
  modified: [linuxmini/local/bin/down_d_impl.py]

key-decisions:
  - "Use --print-to-file %(height)s to extract resolution rather than parsing yt-dlp verbose output"
  - "Show '...' while resolution is resolving during download, 'best' for pending tasks"

patterns-established:
  - "Temp file per download thread for metadata exchange: tmpdir/{task_id}_height.txt"

duration: 3min
completed: 2026-02-11
---

# Quick Task 3: Parse Actual Video Quality from yt-dlp Summary

**Real video resolution display via yt-dlp --print-to-file %(height)s, replacing static quality argument display**

## Performance

- **Duration:** 3 min
- **Started:** 2026-02-11T12:15:59Z
- **Completed:** 2026-02-11T13:07:54Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Quality column now shows actual downloaded resolution (e.g., 720p, 1080p) instead of requested quality
- When using -q best or no quality flag, displays actual resolution once yt-dlp resolves the format
- Resolution updates early in download (during format resolution phase, before significant progress)
- Display handles any numeric resolution (480p, 720p, 1080p, 1440p, 2160p, etc.) via isdigit() check

## Task Commits

Each task was committed atomically:

1. **Task 1: Add --print-to-file to yt-dlp commands and parse actual resolution** - `c89ed15` (feat)

## Files Created/Modified
- `linuxmini/local/bin/down_d_impl.py` - Added height_file param to build_tier_command with --print-to-file flag, height file reading in download_with_progress loop, dynamic quality display in create_progress_table

## Decisions Made
- Used yt-dlp's `--print-to-file %(height)s` to write resolved height to a temp file rather than parsing verbose output -- this is reliable across all tiers including external downloaders since yt-dlp resolves formats before handing off to axel
- Show "..." while downloading if resolution not yet known (vs "best") to indicate resolution is still resolving
- Read height file with OSError handling since the file may be written concurrently by the yt-dlp process

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Quality column complete with actual resolution display
- down_d progress table feature set is now comprehensive (size, quality, speed, ETA)

## Self-Check: PASSED

- FOUND: linuxmini/local/bin/down_d_impl.py
- FOUND: 3-SUMMARY.md
- FOUND: commit c89ed15

---
*Phase: quick-3*
*Completed: 2026-02-11*
