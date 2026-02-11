# Pitfalls: Dotfiles Management

**Research Date:** 2026-02-10
**Confidence:** HIGH

## Critical Pitfalls

### 1. Editing Symlinked Targets Instead of Source Files

**Problem:** Changes made to `~/.config/` files are lost on next `setup.py` run since they're symlinks.

**Warning Signs:**
- Config changes disappear after running `setup.py`
- Git shows no changes despite making edits

**Prevention:**
- Always edit files in `~/.dotfiles/` source locations
- CLAUDE.md already documents this for AI agents
- Consider fish aliases or editor warnings for humans

**Risk Areas:** All config additions, human-driven edits

### 2. Secrets Accidentally Committed in Plaintext

**Problem:** SOPS `.path_regex` rules must be manually extended for each new secrets file.

**Warning Signs:**
- Secrets files not encrypted after adding
- Git status shows unencrypted sensitive files

**Prevention:**
- 5-step checklist: .sops.yaml rule + .gitignore exception + encrypt + verify + test decrypt
- Pre-commit hook to validate SOPS encryption status

**Risk Areas:** New secrets files, new machine configs

### 3. Merge Hierarchy Precedence Violations

**Problem:** Common files can shadow machine-specific overrides in edge cases (broken symlinks, directory-level symlinks).

**Warning Signs:**
- Machine-specific config not taking effect
- Unexpected config values on specific machines

**Prevention:**
- Add `--check-shadows` diagnostic to detect when machine files shadow common
- Explicit logging when merge chooses machine over common

**Risk Areas:** Config refactoring, multi-machine testing

### 4. Applications That Overwrite Symlinks

**Problem:** Apps using atomic-write via `rename()` syscall destroy symlinks.

**Warning Signs:**
- Config symlink becomes regular file
- Changes to dotfiles source no longer reflected

**Prevention:**
- Test every new application with symlinks
- Add to `BACKUP_CONFIGS` if it breaks symlinks
- Document apps that require backup mechanism

**Risk Areas:** Every new application integration

### 5. SOPS Age Key Not Present on New Machines

**Problem:** New/rebuilt machines missing age key can't decrypt secrets.

**Warning Signs:**
- `setup.py` prints SOPS warnings
- MCP servers not configured
- Partial configuration state

**Prevention:**
- Document age key setup in machine bootstrap process
- Provide clear error message with recovery steps

**Risk Areas:** New machine setup, disaster recovery

### 6. Stale Symlink Cleanup

**Problem:** Renamed/removed files leave broken symlinks in `~/.config/` that `setup.py` doesn't detect.

**Warning Signs:**
- `ls -la ~/.config/` shows broken symlinks
- Applications complain about missing config

**Prevention:**
- Add broken-symlink cleanup to `setup.py` deployment phase
- Scan `~/.config/` for symlinks pointing to non-existent dotfiles

**Risk Areas:** Config file renames, deletions, reorganization

## Anti-Patterns

- **Manual fixes outside setup.py:** Defeats declarative principle
- **Bash scripts for setup logic:** Use Python (except fish functions and simple wrappers)
- **Assuming common works everywhere:** Always test machine-specific overrides
- **Forgetting SOPS encryption:** Secrets must be encrypted before commit

## Phase Recommendations

- **Config additions:** Include symlink persistence testing
- **Secrets additions:** Follow 5-step SOPS checklist
- **Refactoring:** Run `--check-shadows` diagnostic
- **Hardening phase:** Add broken-symlink cleanup and shadow detection
