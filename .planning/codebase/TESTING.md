# Testing Patterns

**Analysis Date:** 2026-02-10

## Test Framework

**Runner:**
- No test framework detected (pytest, unittest, vitest not configured)
- No test files found in repository

**Assertion Library:**
- Not applicable; no automated tests present

**Run Commands:**
```bash
# No automated test suite exists
# Testing is manual/ad-hoc:
python setup.py                    # Run full setup (main test path)
python -m setup.env_distribution   # Test individual modules (if __main__ block exists)
```

## Test File Organization

**Location:**
- No dedicated test directory (`tests/`, `test/`, `__tests__/`)
- No test files matching `*_test.py`, `test_*.py`, `*.spec.py` patterns
- Some modules have `if __name__ == "__main__":` blocks for standalone testing

**Naming:**
- Not applicable; no test suite

**Structure:**
- Not applicable; no test suite

## Manual Testing Approach

**Current Testing Strategy:**
The codebase relies on manual testing through the setup process itself. Key validation points:

**Setup.py Main Execution:**
- `setup.py` is the primary integration test
- Executed on each machine to validate the entire dotfiles workflow
- Tests the full dependency chain: merge → symlink → configuration → systemd reload
- Output includes emoji-prefixed status messages that indicate success/failure

**Standalone Module Testing:**
Several modules include `if __name__ == "__main__":` blocks for isolated testing:

`env_distribution.py`:
```python
if __name__ == "__main__":
    # Allow running this script standalone for testing
    dotfiles_dir = Path(__file__).parent.parent
    machine = get_current_machine()
    distribute_env_vars(dotfiles_dir, machine, verbose=True)
```

Run individually:
```bash
python setup/env_distribution.py
```

**File Operation Testing:**
Key areas tested manually during setup:

1. **Symlink Creation** (`symlink_setup.py`):
   - Validates symlinks created correctly
   - Checks for existing symlinks that point to correct targets
   - Warns about external symlinks (not replaced)
   - Output confirms: `✅ {target} -> {source}`

2. **Merge Operations** (`merge_setup.py`):
   - Validates directory merging with progress counter
   - Output shows: `🔀 Merging... ({current}/{total})`
   - Cleanup of broken symlinks reported

3. **Environment Variable Distribution** (`env_distribution.py`):
   - Validates config file generation
   - Tests systemd environment import
   - Hyprland config generation tested on linuxmini

4. **SSH Setup** (`ssh_setup.py`):
   - Validates file existence before symlinking
   - Tests permission setting (mode 0o700, 0o600)
   - Warns if source files missing

5. **System Configuration** (`hosts_setup.py`, `security_setup.py`, `sudoers_setup.py`):
   - Tests for existing configurations (no duplicates)
   - Validates content matches before updating
   - Requires manual sudo permission

## Mocking

**Framework:**
- No mocking framework (unittest.mock, pytest-mock, vitest not present)

**Patterns:**
- Manual isolation through standalone module execution
- File system is used directly (not mocked)
- Subprocess calls execute real commands (intentional for setup)

**What to Mock (if tests were added):**
- Filesystem operations for unit tests (use pathlib with fixtures)
- Subprocess calls that require elevation (sudo, systemctl)
- File I/O that modifies system state

**What NOT to Mock:**
- Core logic of merge/symlink algorithms (test with real files)
- YAML/JSON parsing (test with real config files)
- Path resolution and symlink validation (requires real filesystem behavior)

## Fixtures and Factories

**Test Data:**
- No factory patterns found
- No fixture definitions

**If tests were to be added:**
- Configuration fixtures in `common/etc/test/` or `tests/fixtures/`
- Example config objects as dicts:
  ```python
  MOCK_MACHINE_CONFIG = {
      "is_macos": True,
      "is_linux": False,
  }
  MOCK_MERGE_DIRS = {
      "config": {
          "source": "config",
          "target": "config",
          "symlink": Path.home() / ".config",
          "symlink_mode": "contents",
      }
  }
  ```

**Location:**
- Would go in `tests/fixtures/` or `setup/test_fixtures.py`

## Coverage

**Requirements:**
- No coverage requirements enforced
- No `.coveragerc`, `coverage.json`, or coverage config found

**View Coverage:**
```bash
# Not applicable - no coverage tooling installed
```

## Test Types

**Unit Tests (if implemented):**
- Scope: Individual functions like `expand_home()`, `mask_secrets_in_json()`, `is_sops_encrypted()`
- Approach: Isolated function testing with configuration fixtures
- Key functions to test:
  - `env_distribution.expand_home()` - path expansion logic
  - `backup_setup.mask_secrets_in_json()` - secret masking
  - `symlink_utils.merge_common_into_machine()` - recursive merge logic
  - `config.py` - configuration loading and validation

**Integration Tests (if implemented):**
- Scope: Full setup workflow or major components
- Approach: Create temporary directories, run setup steps, validate results
- Key scenarios:
  - Merge common + machine-specific configs
  - Create symlinks and validate targets
  - Generate environment files and parse them
  - Handle existing configs without collision

**E2E Tests:**
- Not currently used; setup.py itself serves as the E2E test
- Would require: virtual machines or containers with clean state
- Would validate: Full setup on clean system with all machines

## Validation and Checking

**Configuration Validation:**

`env_distribution.py`:
- Validates config file exists: `if not config_file.exists(): raise FileNotFoundError()`
- Validates machine in config: `if "machines" in config and machine in config["machines"]`

`symlink_setup.py`:
- Validates source exists: `if not source_dir.exists(): continue`
- Validates target path safety: `if str(existing_target).startswith(str(dotfiles_dir))`

**Status Indicators:**
All operations report status through print output with emoji prefixes:
- `✅` - Success (file created, config applied)
- `⚠️` - Warning (non-critical issue, skip or fallback)
- `ℹ️` - Information (status update, no action needed)
- `🗑️` - Cleanup (removed broken symlink)
- `❌` - Error (critical failure - uncommon)

**Idempotency:**
Setup is designed to be idempotent; can be run multiple times safely:
- Checks existing symlinks before replacing
- Validates config content matches before updating
- Uses marker comments in config files (`# === AUTO-GENERATED ===`)
- Skips duplicate entries (hosts, sudoers, crontab)

## Testing Gaps

**Untested Areas:**

1. **Error Recovery** (`hosts_setup.py`, `sudoers_setup.py`):
   - What happens if sudo elevation fails silently?
   - Files: `setup/hosts_setup.py`, `setup/sudoers_setup.py`, `setup/security_setup.py`
   - Risk: Silent failures if permissions insufficient
   - Priority: HIGH - system configuration errors should be visible

2. **Complex Merge Logic** (`merge_setup.py`):
   - Recursive directory merging with symlink handling
   - `.gitignore` generation with de-duplication
   - Files: `setup/merge_setup.py`, `setup/symlink_utils.py`
   - Risk: Silent corruption of `.gitignore` or broken symlinks
   - Priority: HIGH - core merge logic needs verification

3. **Secret Masking** (`backup_setup.py`):
   - JSON path parsing with `connections[*].field` pattern
   - Secret injection/masking on backup/restore
   - Files: `setup/backup_setup.py`
   - Risk: Secrets accidentally committed or masked incorrectly
   - Priority: HIGH - security-critical

4. **Environment Variable Expansion** (`env_distribution.py`):
   - PATH merging with $PATH variable
   - Home directory expansion with `~` and `$HOME`
   - Machine-specific vs global overrides
   - Files: `setup/env_distribution.py`
   - Risk: Incorrect PATH leads to shell failures
   - Priority: MEDIUM - manifests as user-visible issues

5. **Crontab Management** (`crontab_setup.py`):
   - Parsing crontab entry identifiers
   - Merging managed entries with existing crontab
   - Sudo crontab special handling
   - Files: `setup/crontab_setup.py`
   - Risk: Duplicate cron jobs, missing backups
   - Priority: MEDIUM - doesn't break setup but impacts functionality

6. **Cross-Platform Logic** (`decrypt-secrets.sh`, `machines.py`):
   - macOS vs Linux conditional logic
   - Hostname detection differences (Linux: `/etc/hostname`, macOS: `hostname -s`)
   - Runtime directory detection (`XDG_RUNTIME_DIR` fallback)
   - Files: `common/scripts/decrypt-secrets.sh`, `machines.py`
   - Risk: Setup fails on unexpected OS/configuration
   - Priority: MEDIUM - affects both platforms equally

7. **Subprocess Call Error Handling** (all setup modules):
   - Many subprocess calls use `check=False` or missing `check`
   - Silent failures not propagated upward
   - Files: `setup/*.py` (systemd_setup, desktop_setup, etc.)
   - Risk: Failed operations reported as success
   - Priority: MEDIUM - affects visibility into failures

## Suggested Test Additions

If testing framework were added (pytest recommended):

```bash
# Run tests:
pytest tests/                      # All tests
pytest tests/test_env_dist.py      # Single module
pytest tests/ -k "merge"           # By pattern
pytest tests/ --cov=setup          # With coverage
```

**Priority Test Files:**
1. `tests/test_env_distribution.py` - Validate env var expansion and merging
2. `tests/test_merge_setup.py` - Validate symlink and .gitignore generation
3. `tests/test_backup_setup.py` - Validate secret masking
4. `tests/test_symlink_utils.py` - Validate recursive merge logic

---

*Testing analysis: 2026-02-10*
