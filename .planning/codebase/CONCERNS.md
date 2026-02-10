# Codebase Concerns

**Analysis Date:** 2026-02-10

## Tech Debt

**Bare exception handling in backup setup:**
- Issue: `setup/backup_setup.py` line 54 uses bare `except:` clause which catches all exceptions including KeyboardInterrupt and SystemExit
- Files: `setup/backup_setup.py`
- Impact: Errors in file checking are silently ignored without logging or debugging capability; can mask real errors
- Fix approach: Replace `except:` with `except (OSError, IOError, json.JSONDecodeError)` to catch specific expected errors only

**Subprocess calls without output capture:**
- Issue: Several setup modules call `subprocess.run()` without `capture_output=True` or `text=True`, making error diagnosis difficult
- Files: `setup/beads_setup.py`, `setup/crontab_setup.py`, `setup/dictation_setup.py`, `setup/env_distribution.py`, `setup/pacman_setup.py`
- Impact: When subprocess commands fail, no error output is captured for troubleshooting; users only see returncode
- Fix approach: Add `capture_output=True, text=True` to all subprocess calls and log stderr on failure

**Hardcoded subprocess.run without error capture in PAM setup:**
- Issue: `setup/pam_setup.py` line 68-70 runs sudo backup without capturing output or checking for errors
- Files: `setup/pam_setup.py`
- Impact: If backup fails silently, PAM file may be corrupted or overwritten without user knowledge
- Fix approach: Add `capture_output=True, text=True` and verify success before proceeding

**String replacement for secret injection is fragile:**
- Issue: `setup/backup_setup.py` lines 145-148 use simple string replacement to inject secrets into JSON, not proper JSON parsing
- Files: `setup/backup_setup.py`
- Impact: If placeholder appears anywhere else in the JSON (e.g., in comments or nested values), it will be incorrectly replaced; could corrupt config files
- Fix approach: Parse JSON, update specific fields, then serialize back to JSON

## Known Bugs

**Subprocess permission errors in SSH setup:**
- Symptoms: Setup may fail if `chmod 600` commands fail on SSH config files (e.g., permission denied)
- Files: `setup/ssh_setup.py` lines 25, 30, 41
- Trigger: Running setup with read-only SSH config files or on systems with restrictive permissions
- Workaround: Manually chmod SSH files before running setup.py, or run with elevated privileges

**Symlink cleanup can break on circular symlinks:**
- Symptoms: Setup fails with OSError when cleaning up broken symlinks in `setup/symlink_utils.py`
- Files: `setup/symlink_utils.py` lines 56-68
- Trigger: If a broken symlink points to itself or forms a circular reference
- Workaround: Manually delete problematic symlinks before running setup.py

**Crontab parsing assumes specific comment format:**
- Symptoms: Crontab entries without "# managed:dotfiles:" marker are left in crontab but may become orphaned
- Files: `setup/crontab_setup.py` lines 47-52
- Trigger: Manually editing crontab entries or mixing managed/unmanaged entries
- Workaround: Maintain strict comment format and don't manually edit managed entries

## Security Considerations

**PAM configuration without validation:**
- Risk: Installing incorrect PAM configs could lock user out of system completely
- Files: `setup/pam_setup.py`
- Current mitigation: Basic check for `pam_unix.so` presence; backup created before install
- Recommendations: Add more comprehensive PAM syntax validation; test in container/VM first; document recovery steps prominently

**Sudoers file modifications without visudo validation in all cases:**
- Risk: Invalid sudoers syntax can lock out sudo access permanently
- Files: `setup/sudoers_setup.py` lines 39-41
- Current mitigation: `visudo -cf` validates syntax before install
- Recommendations: Keep backup clear and documented; print recovery instructions on success

**SSH authorized_keys symlink could expose keys:**
- Risk: If symlink permissions are wrong, SSH keys could be readable by other users
- Files: `setup/ssh_setup.py` line 42
- Current mitigation: SSH directory created with 0o700 permissions
- Recommendations: Verify symlink inherits parent directory permissions; add explicit chmod after symlink creation

**/etc/hosts entries use simple marker-based approach:**
- Risk: If marker lines are accidentally deleted, next setup run may duplicate entries
- Files: `setup/hosts_setup.py` lines 28-38
- Current mitigation: Checks for marker before adding entries
- Recommendations: Implement proper parsing that updates existing block rather than just checking marker

**Secrets masking in config backups can leak via temp files:**
- Risk: JSON parsing and string operations create temporary string objects that could be dumped to swap/pagefile
- Files: `setup/backup_setup.py` lines 91-97
- Current mitigation: None
- Recommendations: Use secure string handling library or clear sensitive strings from memory; consider not storing masked config in gitignored files

## Performance Bottlenecks

**Large recursive merge operation with no progress indication for deep hierarchies:**
- Problem: Merging config directories with deep nesting (10+ levels) blocks terminal output during progress calculation
- Files: `setup/merge_setup.py` lines 12-23
- Cause: `count_files_to_process()` recursively counts entire tree before starting merge, then updates progress on every file
- Improvement path: Remove pre-count pass; show relative progress based on directory level instead; use concurrent file operations for shallow directories

**PAM/sudoers/security file comparison reads entire files into memory:**
- Problem: Each setup run reads and compares complete file content to check if identical
- Files: `setup/pam_setup.py` lines 40-44, `setup/sudoers_setup.py` lines 27-32, `setup/security_setup.py` lines 38-43
- Cause: Using `read_text()` on potentially large config files
- Improvement path: Use file hash comparison (SHA256) for large files, or just trust timestamps for same-size files

## Fragile Areas

**Symlink resolution with circular references:**
- Files: `setup/symlink_setup.py`, `setup/systemd_setup.py`
- Why fragile: `target.resolve()` can fail or hang on circular symlinks; exception handling catches OSError but other errors may propagate
- Safe modification: Always wrap resolve() calls in try-except; consider using `resolve(strict=False)` consistently
- Test coverage: No tests for circular symlink scenarios; needs unit tests

**Environment variable path manipulation and expansion:**
- Files: `setup/env_distribution.py` lines 32-39
- Why fragile: Manual string replacement of `$HOME` and `~` without proper path escaping could fail with special characters in home directory path
- Safe modification: Use `pathlib.Path.expanduser()` instead of manual string replacement
- Test coverage: No tests for edge cases like home directories with spaces or special characters

**Machine configuration assumptions:**
- Files: `machines.py`
- Why fragile: Hostname-based machine detection is brittle - hostname can change or not match expected value
- Safe modification: Add fallback detection based on `/etc/hostname`, uname, or config file; allow override via env var
- Test coverage: Only tested with exact hostname matches

**Backup config secrets masking with complex JSON paths:**
- Files: `setup/backup_setup.py` lines 26-44
- Why fragile: Simple json_path parser only handles `connections[*].field` patterns; breaks with nested arrays or complex structures
- Safe modification: Use proper JSON path library (jsonpath-rw) or use jq-style queries; add schema validation
- Test coverage: Only tested with basic flat structures; no tests for edge cases

## Test Coverage Gaps

**Setup script system-wide modifications not tested:**
- What's not tested: PAM file installation, sudoers modification, /etc/hosts changes, systemd service reloads
- Files: `setup/pam_setup.py`, `setup/sudoers_setup.py`, `setup/hosts_setup.py`, `setup/systemd_setup.py`
- Risk: Errors in system configuration could lock user out or break system functionality
- Priority: HIGH - These are safety-critical operations

**Symlink creation and replacement edge cases:**
- What's not tested: Broken symlinks, circular symlinks, symlink to non-existent paths, permission denied scenarios
- Files: `setup/symlink_setup.py`, `setup/symlink_utils.py`
- Risk: Silent failures or incomplete setups that leave system in inconsistent state
- Priority: HIGH

**Multi-machine merge logic with conflicts:**
- What's not tested: What happens when common/config/app conflicts with linuxcommon/config/app conflicts with machine/config/app
- Files: `setup/merge_setup.py`
- Risk: Merged configs could have unexpected precedence; hardest-to-debug issue
- Priority: MEDIUM

**Subprocess error handling with different exit codes:**
- What's not tested: What happens when subprocess exits with various non-zero codes, stderr vs stdout capture
- Files: All `setup/*.py` modules
- Risk: Inconsistent error reporting makes troubleshooting difficult
- Priority: MEDIUM

**Environment variable expansion with special characters:**
- What's not tested: Paths with spaces, colons, quotes, or other shell-special characters in PATH or other env vars
- Files: `setup/env_distribution.py`
- Risk: Generated env files could have malformed PATH entries, breaking shell environment
- Priority: MEDIUM

## Scaling Limits

**Debug output in production code:**
- Current state: `switch_ws_on_monitor.py` has 15+ hardcoded print statements prefixed with [DEBUG]
- Limit: Every invocation prints debug spam to stdout; no way to disable
- Scaling path: Implement proper logging module; use logging.DEBUG level instead of print()
- Files: `linuxmini/scripts/hyprland/hypr_window_ops/hypr_window_ops/switch_ws_on_monitor.py`

**Crontab entry management without deduplication:**
- Current state: Crontab entries stored in text file; identifier-based matching is string-dependent
- Limit: If two identifiers are similar or identifier format changes, entries can be duplicated
- Scaling path: Use structured format (YAML/JSON) for crontab entries instead of comments; implement UUIDs
- Files: `setup/crontab_setup.py`

## Dependencies at Risk

**YAML library without version pinning:**
- Risk: `setup/env_distribution.py` imports `yaml` without version constraint in setup.py
- Impact: yaml 6.0+ has breaking changes for round-trip preservation
- Migration plan: Add explicit `pyyaml>=5.4,<6.0` to requirements or use setup.py dependencies comment; test with different versions

**subprocess.run capture_output parameter:**
- Risk: `capture_output` parameter was added in Python 3.7; codebase doesn't document minimum Python version
- Impact: Running on Python 3.6 or earlier will fail with TypeError
- Migration plan: Document Python 3.8+ requirement; add version check in setup.py; consider using older `stdout=PIPE, stderr=PIPE` syntax for compatibility

## Missing Critical Features

**No dry-run mode:**
- Problem: Setup script makes actual changes to system without option to preview
- Blocks: Testing setup on new machines; verifying changes before applying
- Implementation: Add `--dry-run` flag that logs planned changes but doesn't execute sudo commands or create symlinks

**No setup rollback functionality:**
- Problem: If setup fails halfway through, manual cleanup is needed
- Blocks: Safe re-running on partially-configured systems
- Implementation: Add checkpoint system; track all modifications; provide `--rollback` command

**No setup idempotency guarantee:**
- Problem: Running setup.py multiple times can produce different results (e.g., symlink replacement, crontab deduplication)
- Blocks: Safe automation and CI/CD integration
- Implementation: Document idempotency assumptions; add tests that run setup twice and verify identical results

**No per-machine setup verification:**
- Problem: After setup completes, no way to verify all configs were applied correctly
- Blocks: Ensuring consistent state across machines
- Implementation: Add `verify` subcommand that checks symlinks exist, permissions correct, services loaded, etc.

---

*Concerns audit: 2026-02-10*
