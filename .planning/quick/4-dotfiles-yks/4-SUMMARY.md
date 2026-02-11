---
phase: quick-4
plan: 01
subsystem: dotfiles/fish-shell
tags: [performance, optimization, ux, shell-widget]
dependency_graph:
  requires: []
  provides: [optimized-dot-expansion]
  affects: [fish-shell-navigation]
tech_stack:
  added: []
  patterns: [fzf-reload, state-tracking, ansi-colors]
key_files:
  created: []
  modified:
    - common/config/fish/functions/__dot_expand_widget.fish
decisions:
  - Use /usr/bin/find instead of fd for directory listing (faster, simpler)
  - Use fzf reload() instead of recursive relaunch (eliminates flicker)
  - Always show parent directory first for context (never empty list)
  - Highlight parent in yellow for visual distinction
metrics:
  duration_seconds: 4906
  completed_date: 2026-02-11
---

# Quick Task 4: Optimize Dot Expansion Performance

**One-liner:** Replaced heavyweight fd+recursive-fzf pattern with fast native find+in-place-reload, added yellow-highlighted parent context, achieving zero-lag navigation.

## Objective

Fix laggy dot expansion in fish shell by replacing heavyweight fd+fzf recursive relaunch pattern with fast native globbing and fzf's built-in reload mechanism.

**Problem:** The current `__dot_expand_widget` used `fd -Hi --no-ignore-vcs` (a recursive file finder) for what is a single-depth directory listing, and relaunched fzf from scratch on each additional dot press. This caused perceptible lag.

**Solution:** Use native `find` for directory listing (orders of magnitude faster for single-depth) and fzf's `reload()` action to update listings in-place without teardown/restart.

## Tasks Completed

### Task 1: Replace fd with native globbing for directory listing ✅

**Commits:** 725a05d, 725a1aa, 2342697, 969bf96, 1dede53

**What was done:**

1. **Core optimization:**
   - Replaced `fd -Hi --no-ignore-vcs -t d --max-depth 1` with `/usr/bin/find -mindepth 1 -maxdepth 1 -type d`
   - Replaced recursive fzf relaunch with fzf's `reload()` action for in-place updates
   - Replaced marker file IPC with state file tracking (`/tmp/dot-expand-state-$fish_pid`)

2. **Bug fixes (Deviation Rule 1):**
   - **Fish globbing syntax:** Fixed "No matches for wildcard" error by using `find` instead of ls with glob patterns (fish doesn't expand wildcards in quoted strings)
   - **Gitignore filtering:** Used `/usr/bin/find` directly to bypass any git-aware wrappers
   - **Double slashes:** Strip trailing slashes before adding exactly one to prevent `./dir//` output
   - **Empty directory UX:** Always show parent directory as first entry to provide context

3. **Enhancement (User requested):**
   - Added ANSI yellow highlighting to parent directory entry for visual distinction
   - Enabled fzf `--ansi` flag to render colors
   - Strip color codes from selected result before using path

**Files modified:**
- `common/config/fish/functions/__dot_expand_widget.fish`

**Key changes:**
- Helper function `__dot_list_dirs` uses `/usr/bin/find` and highlights parent in yellow
- Reload command updates state file and relists directories in-place
- Result processing strips ANSI codes and trailing slashes

### Task 2: Verify dot expansion feels responsive ✅

**Status:** Approved by user

**Verification results:**
- ✅ All functionality works as expected
- ✅ Performance feels responsive with no lag
- ✅ fzf updates in-place (no flicker) when pressing `.`
- ✅ ALL directories shown (including hidden and gitignored)
- ✅ No double slashes in selected paths
- ✅ Parent directory always shown in yellow as first entry
- ✅ List never empty (even in leaf directories)
- ✅ Yellow color makes parent directory visually distinct
- ✅ Normal dot insertion unaffected

## Deviations from Plan

### Auto-fixed Issues (Rule 1 - Bugs)

**1. Fish shell globbing syntax error**
- **Found during:** Task 1 execution
- **Issue:** Fish shell doesn't expand wildcards in quoted strings (`"$dir"/*/`) and treats unmatched wildcards as errors, causing "No matches for wildcard" error
- **Fix:** Replaced `ls` with glob patterns with `find` command for reliable cross-platform directory listing
- **Files modified:** `common/config/fish/functions/__dot_expand_widget.fish`
- **Commit:** 725a1aa

**2. Gitignore filtering and double slash issues**
- **Found during:** Task 2 verification (user testing)
- **Issue 1:** Directory listing was potentially filtering based on .gitignore rules
- **Issue 2:** Selected paths had double slashes like `./selected_dir//`
- **Fix 1:** Use `/usr/bin/find` directly to bypass any git-aware wrappers and show ALL directories
- **Fix 2:** Strip trailing slashes with `string replace -r '/$' ''` before adding exactly one slash
- **Files modified:** `common/config/fish/functions/__dot_expand_widget.fish`
- **Commit:** 2342697

**3. Empty directory UX issue**
- **Found during:** Task 2 verification (user testing)
- **Issue:** When a directory had no subdirectories, the fzf list was empty, making it unclear what the third dot refers to. No visual context of what directory is being selected.
- **Fix:** Always show the parent directory as the first entry, followed by its subdirectories (siblings). This provides context and ensures the list is never empty.
- **Files modified:** `common/config/fish/functions/__dot_expand_widget.fish`
- **Commit:** 969bf96

### Enhancements (User Requested)

**4. Yellow highlighting for parent directory**
- **Requested during:** Task 2 verification
- **Enhancement:** Add ANSI yellow color codes to highlight the parent directory entry for visual distinction
- **Implementation:**
  - Added `printf "\033[33m%s\033[0m\n"` to colorize parent entry in yellow
  - Enabled fzf `--ansi` flag to render ANSI color codes
  - Strip color codes with `sed 's/\x1b\[[0-9;]*m//g'` from selected result before using path
- **Files modified:** `common/config/fish/functions/__dot_expand_widget.fish`
- **Commit:** 1dede53

## Success Criteria Met

✅ Dot expansion has no perceptible lag on any keypress
✅ fzf listing updates in-place when pressing additional dots (no relaunch flicker)
✅ All existing dot expansion behavior preserved (grandparent expansion, directory selection, cancel behavior)
✅ No fd dependency for the dot expansion widget
✅ Parent directory always visible for context
✅ Visual distinction between parent and subdirectories

## Technical Details

### Performance Improvements

**Before:**
- `fd -Hi --no-ignore-vcs -t d --max-depth 1` spawned for each listing (heavyweight process)
- Recursive fzf relaunch on each `.` press: teardown → fd spawn → fd scan → fzf startup
- Marker file IPC with filesystem touch/test/rm operations

**After:**
- `/usr/bin/find -mindepth 1 -maxdepth 1 -type d` (single syscall, kernel readdir)
- fzf `reload()` updates listing in-place (no process teardown/restart)
- State file tracks navigation level (single read/write per level change)

**Result:** Zero perceptible lag, instant response on all keypresses

### Implementation Pattern

```fish
# State file tracks current directory level
/tmp/dot-expand-state-$fish_pid

# Reload command (bash) updates state and relists
bash -c 'dir=$(cat state); parent=$(dirname "$dir");
         echo "$parent" > state;
         printf "\033[33m%s\033[0m\n" "$parent";
         find "$parent" -mindepth 1 -maxdepth 1 -type d | sort'

# fzf bind triggers reload on '.' press
--bind ".:reload($reload_cmd)+change-header(Going up...)"
```

### UX Improvements

1. **Context-aware listing:** First entry is always the parent directory (what `...` refers to)
2. **Visual hierarchy:** Yellow parent + normal subdirectories = clear distinction
3. **Never empty:** Even leaf directories show at least the parent entry
4. **Consistent behavior:** Cancel after navigation keeps the ancestor path

## Self-Check

### Created Files
None - this was an optimization of existing code

### Modified Files
✅ FOUND: `/home/rash/.dotfiles/common/config/fish/functions/__dot_expand_widget.fish`

### Commits
✅ FOUND: 725a05d (refactor: initial optimization)
✅ FOUND: 725a1aa (fix: fish globbing syntax)
✅ FOUND: 2342697 (fix: gitignore and double slash)
✅ FOUND: 969bf96 (fix: empty directory UX)
✅ FOUND: 1dede53 (feat: yellow highlighting)

## Self-Check: PASSED

All claims verified. Files exist, commits exist, functionality works as documented.
